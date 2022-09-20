# -*- coding: utf-8 -*-
import asyncio
import json
import os
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

import disnake
from disnake import ApplicationCommandInteraction
from disnake.ext import commands


class Thread(commands.Cog):
    def __init__(self, bot):
        """Initialize the cog"""
        self.bot: commands.InteractionBot = bot
        self.forum_channel: disnake.ForumChannel = (
            None  # cannot fetch it here since the cog is initialized before the connection
        )
        self.forum_channel_id: int = int(os.getenv("FORUM_CHANNEL"))
        try:
            with open("cogs/Thread/tags.json") as json_file:
                self.tag_role_map: Dict[str, List[int]] = json.load(json_file)
        except json.JSONDecodeError:
            self.tag_role_map: Dict[str, List[int]] = {}
            self.save_tag_role_map()

    def save_tag_role_map(self) -> None:
        with open("cogs/Thread/tags.json", "w") as json_file:
            json.dump(self.tag_role_map, json_file, indent=4)

    def tag_from_name(self, name: str) -> Optional[disnake.ForumTag]:
        return next((tag for tag in self.forum_channel.available_tags if tag.name == name), None)

    def role_from_name(self, guild: disnake.Guild, name: str) -> Optional[disnake.Role]:
        return next((role for role in guild.roles if role.name == name), None)

    @commands.slash_command(name="tag", default_member_permissions=disnake.Permissions.all())
    async def tag(self, inter):
        pass

    @tag.sub_command(name="add", description="Lier un tag du forum avec un role.")
    async def tag_link(
        self,
        inter: ApplicationCommandInteraction,
        tag: str = commands.Param(description="Le tag du forum auquel lier un role."),
        role: str = commands.Param(
            description="Le role à lier au tag. Les rôles déjà liés à ce tag ne sont pas affichés."
        ),
    ):
        await inter.response.defer(ephemeral=True)

        # Link the role to the tag (either add it to the existing list of role for this tag, or create a new list)
        _tag = self.tag_from_name(tag)
        if _tag == None:
            raise ValueError(f'Unable to retrieve tag from name "{tag}"')

        _role = self.role_from_name(inter.guild, role)
        if _role == None:
            raise ValueError(f'Unable to retrieve role from name "{role}"')

        if str(_tag.id) in self.tag_role_map.keys():
            roles = self.tag_role_map.get(str(_tag.id))
            if _role.id in roles:
                await inter.edit_original_message(
                    embed=disnake.Embed(description=f"⚠️ Le role {role} est déjà lié avec le tag {tag}").set_footer(
                        text="Tu peux rejeter ce message pour le faire disparaitre."
                    )
                )
                return
            roles.append(_role.id)
        else:
            self.tag_role_map.setdefault(str(_tag.id), [_role.id])
        self.save_tag_role_map()

        # Send a confirmation message with all the roles linked to the tag
        linked_roles: List[disnake.Role] = [inter.guild.get_role(id) for id in self.tag_role_map.get(str(_tag.id))]

        await inter.edit_original_message(
            embed=disnake.Embed(
                title=f"🔗 __**Tag**__ {_tag.emoji} {_tag.name}",
                color=disnake.Colour.green(),
                description=f"{_tag.emoji} **{_tag.name}** et **{_role.mention}** sont maintenant liés",
            )
            .add_field(
                name="__Roles liés :__",
                value="\n> " + "\n> ".join([role.mention for role in linked_roles])
                if linked_roles
                else "*Aucun role lié*",
            )
            .set_footer(text="Tu peux rejeter ce message pour le faire disparaitre.")
        )

    @tag.sub_command(name="remove", description="Delier un tag du forum avec un role.")
    async def tag_unlink(
        self,
        inter: ApplicationCommandInteraction,
        tag: str = commands.Param(description="Le tag du forum duquel délier un role."),
        role: str = commands.Param(description="Le role à lier au tag. Seuls les roles liés à ce tag sont affichés."),
    ):
        await inter.response.defer(ephemeral=True)

        # Link the role to the tag (either add it to the existing list of role for this tag, or create a new list)
        _tag = self.tag_from_name(tag)
        if _tag == None:
            raise ValueError(f'Unable to retrieve tag from name "{tag}"')

        _role = self.role_from_name(inter.guild, role)
        if _role == None:
            raise ValueError(f'Unable to retrieve role from name "{role}"')

        if str(_tag.id) not in self.tag_role_map.keys():
            raise KeyError(f"Tag {tag} is not in database")

        roles = self.tag_role_map.get(str(_tag.id))
        if _role.id not in roles:
            raise ValueError(f"Role {_role.name} is not linked to tag {tag}")

        roles.remove(_role.id)
        self.save_tag_role_map()

        # Send a confirmation message with all the roles linked to the tag

        linked_roles: List[disnake.Role] = [inter.guild.get_role(id) for id in self.tag_role_map.get(str(_tag.id))]
        await inter.edit_original_message(
            embed=disnake.Embed(
                title=f"🧹 __**Tag**__ {_tag.emoji} {_tag.name}",
                color=disnake.Colour.green(),
                description=f"{_tag.emoji} **{_tag.name}** et **{_role.mention}** ne sont plus liés.",
            )
            .add_field(
                name="__Roles liés :__",
                value="\n> " + "\n> ".join([role.mention for role in linked_roles])
                if linked_roles
                else "*Aucun role lié*",
                inline=False,
            )
            .set_footer(text="Tu peux rejeter ce message pour le faire disparaitre.")
        )

    @tag_link.autocomplete("tag")
    @tag_unlink.autocomplete("tag")
    async def tag_link_autocomplete(self, inter: ApplicationCommandInteraction, value: str):
        if self.forum_channel == None:
            channel = inter.guild.get_channel(self.forum_channel_id)
            if isinstance(channel, disnake.ForumChannel):
                self.forum_channel = channel
            else:
                raise TypeError(
                    f'"FORUM_CHANNEL" should correspond to a forum channel, but the provided one is a "{type(channel)}"'
                )
        return [tag.name for tag in self.forum_channel.available_tags if tag.name.lower().startswith(value.lower())]

    @tag_link.autocomplete("role")
    async def tag_link_autocomplete(self, inter: ApplicationCommandInteraction, value: str):
        tag_name = inter.filled_options.get("tag")
        if tag_name == "":
            return [inter.guild.roles]
        else:
            tag = self.tag_from_name(tag_name)
            if tag == None:
                raise ValueError(f'Unable to retrieve tag from name "{tag_name}"')
            role_already_linked_ids = self.tag_role_map.get(str(tag.id), [])
            return [
                role.name
                for role in inter.guild.roles
                if (role.id not in role_already_linked_ids and role.name.lower().startswith(value.lower()))
            ]

    @tag_unlink.autocomplete("role")
    async def tag_unlink_autocomplete(self, inter: ApplicationCommandInteraction, value: str):
        tag_name = inter.filled_options.get("tag")
        if tag_name == "":
            return [inter.guild.roles]
        else:
            tag = self.tag_from_name(tag_name)
            if tag == None:
                raise ValueError(f'Unable to retrieve tag from name "{tag_name}"')
            role_already_linked_ids = self.tag_role_map.get(str(tag.id), [])
            return [
                role.name
                for role in inter.guild.roles
                if (role.id in role_already_linked_ids and role.name.lower().startswith(value.lower()))
            ]

    @tag.sub_command(name="view", description="Voir tous les roles liés à un tag")
    async def tag_view(
        self,
        inter: ApplicationCommandInteraction,
        tag: str = commands.Param(description="Le tag à voir. Seuls les tags avec au moins un role lié sont affichés."),
    ):
        await inter.response.defer(ephemeral=True)

        _tag = self.tag_from_name(tag)
        if _tag == None:
            raise ValueError(f"Unable to retrieve tag fro mname {tag}")

        linked_roles: List[disnake.Role] = [inter.guild.get_role(id) for id in self.tag_role_map.get(str(_tag.id))]

        await inter.edit_original_message(
            embed=disnake.Embed(title=f"__**Tag**__ {_tag.emoji} {_tag.name}", color=disnake.Colour.green())
            .add_field(
                name="__Roles liés :__",
                value="\n> " + "\n> ".join([role.mention for role in linked_roles])
                if linked_roles
                else "*Aucun role lié*",
                inline=False,
            )
            .set_footer(text="Tu peux rejeter ce message pour le faire disparaitre.")
        )

    @tag_view.autocomplete("tag")
    async def tag_link_autocomplete(self, inter: ApplicationCommandInteraction, value: str):
        if self.forum_channel == None:
            channel = inter.guild.get_channel(self.forum_channel_id)
            if isinstance(channel, disnake.ForumChannel):
                self.forum_channel = channel
            else:
                raise TypeError(
                    f'"FORUM_CHANNEL" should correspond to a forum channel, but the provided one is a "{type(channel)}"'
                )
        return [
            tag.name
            for tag in self.forum_channel.available_tags
            if self.tag_role_map.get(str(tag.id)) and tag.name.lower().startswith(value.lower())
        ]

    @commands.Cog.listener("on_thread_create")
    async def thread_create(self, thread: disnake.Thread):

        # Make a list of all the members that has at least on role corresponding to the tags of the thread
        members_to_notify: List[disnake.Member] = []
        for tag in thread.applied_tags:
            role_ids: Union[List[int], None] = self.tag_role_map.get(str(tag.id), None)
            if role_ids:
                for role_id in role_ids:
                    role = thread.guild.get_role(role_id)
                    if role:
                        [members_to_notify.append(member) for member in role.members if member not in members_to_notify]

        # End here if nobody to notify
        if not members_to_notify:
            return

        # Added all selected user to the thread
        for member in members_to_notify:
            await thread.add_user(member)

        # Wait until the first message if available to the API
        timer: float = 10.0
        sec_to_wait: float = 0.5
        while thread.last_message == None and timer > 0:
            await asyncio.sleep(sec_to_wait)
            timer -= sec_to_wait

        # Create the embed that will be sent as notification
        if thread.last_message:
            max_text_size = 100
            text = thread.last_message.content
            if len(text) > max_text_size:
                text = text[: max_text_size - 3] + "..."
            text = f'"{text}"'
            text = "> " + "\n> ".join([f"*{line}*" for line in text.splitlines()])
        else:
            text = "*Unable to load the message*"

        embed = (
            disnake.Embed(
                title="**Nouvelle discussion te concernant**",
                description=f"> __**{thread.name}**__\n{text}\n\n[Aller à la discussion]({thread.jump_url})",
                color=disnake.Colour.teal(),
            )
            .add_field(
                name="**Tags :**",
                value="\n".join([f"{tag.emoji} {tag.name}" for tag in thread.applied_tags]),
                inline=False,
            )
            .set_thumbnail(url="https://i.imgur.com/BHgic3o.png")
        )

        # Send the notif to all selected members
        for member in members_to_notify:
            await member.send(embed=embed)


def setup(bot: commands.InteractionBot):
    bot.add_cog(Thread(bot))
