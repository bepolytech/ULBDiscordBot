# -*- coding: utf-8 -*-
import json
import logging
import os
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

import disnake
from disnake import ApplicationCommandInteraction
from disnake.ext import commands

from bot.bot import Bot


class Thread(commands.Cog):
    def __init__(self, bot):
        """Initialize the cog"""
        self.bot: Bot = bot
        self.bep_server_id = int(os.getenv("BEP_SERVER"))
        self.forum_channel_id: int = int(os.getenv("FORUM_CHANNEL"))

        try:
            with open("cogs/Thread/tags.json") as json_file:
                self.tag_role_map: Dict[str, List[int]] = json.load(json_file)
        except json.JSONDecodeError:
            self.tag_role_map: Dict[str, List[int]] = {}
            self.save_tag_role_map()
        except FileNotFoundError:
            self.tag_role_map: Dict[str, List[int]] = {}
            self.save_tag_role_map()

    ### Utility Functions ###

    def save_tag_role_map(self) -> None:
        """Save the tag_role_map to the json file"""
        with open("cogs/Thread/tags.json", "w") as json_file:
            json.dump(self.tag_role_map, json_file, indent=4)

    async def tag_from_name(self, guild: disnake.Guild, name: str) -> Optional[disnake.ForumTag]:
        """Retrieve ForumTag of the forum_channel from his name

        Parameters
        ----------
        guild: :class:`disnake.Guild`
            The guild that contains the role to retrieve
        name: :class:`str`
            The name of the ForumTag to retrieve

        Returns
        -------
        Optional[:class:`disnake.ForumTag`]
            The retrieved ForumTag
        """
        tag: disnake.ForumTag = next(
            (tag for tag in (await guild.fetch_channel(self.forum_channel_id)).available_tags if tag.name == name), None
        )
        if tag:
            return tag
        else:
            raise ValueError(f"Unable to retrieve tag from {name=}")

    async def role_from_name(self, guild: disnake.Guild, name: str) -> Optional[disnake.Role]:
        """Retrieve role of a given guild from his name

        Parameters
        ----------
        guild: :class:`disnake.Guild`
            The guild that contains the role to retrieve
        name: :class:`str`
            The name of the role to retrieve

        Returns
        -------
        Optional[:class:`disnake.Role`]
            The retrieved role
        """
        role: disnake.Role = next((role for role in await guild.fetch_roles() if role.name == name), None)
        if role:
            return role
        else:
            raise ValueError(f"Unable to retrieve role from {name=}")

    async def thread_from_name(self, guild: disnake.Guild, name: str) -> Optional[disnake.Thread]:
        """Retrieve thread of a given guild from his name

        Parameters
        ----------
        guild: :class:`disnake.Guild`
            The guild that contains the thread to retrieve
        name: :class:`str`
            The name of the thread to retrieve

        Returns
        -------
        Optional[:class:`disnake.Thread`]
            The retrieved thread
        """
        forum = await guild.fetch_channel(self.forum_channel_id)
        threads = forum.threads
        thread: disnake.Thread = next((thread for thread in threads if thread.name == name), None)
        if thread:
            return thread
        else:
            raise ValueError(f"Unable to retrieve thread from {name=}")

    def thread_to_notif(self, thread: disnake.Thread) -> Tuple[disnake.Embed, disnake.ui.Button]:
        """Convert a thread into an embed and a button to be send together as notification

        Parameters
        ----------
        thread: :class:`disnake.Thread`
            The thread to convert

        Returns
        -------
        Tuple[:class:`disnake.Embed`, :class:`disnake.ui.Button`]
            A Tuple containing the embed and the button
        """
        embed = (
            disnake.Embed(
                title=f"🗨️ ***{thread.name}***",
                color=disnake.Colour.teal(),
            )
            .set_author(name="Nouvelle discussion te concernant")
            .add_field(
                name="__**Tags :**__",
                value="> " + "\n> ".join([f"{tag.emoji} {tag.name}" for tag in thread.applied_tags])
                if thread.applied_tags
                else "*no tags*",
                inline=False,
            )
            .set_thumbnail(url="https://i.imgur.com/BHgic3o.png")
        )
        button = disnake.ui.Button(style=disnake.ButtonStyle.url, url=thread.jump_url, label="Aller à la discussion")
        return (embed, button)

    ### Discord Commands & Sub commands ####

    @commands.slash_command(
        name="thread_link",
        default_member_permissions=disnake.Permissions.all(),
        guild_ids=[int(os.getenv("BEP_SERVER"))],
    )
    async def thread_link(self, inter):
        pass

    @thread_link.sub_command(name="add", description="Lier un tag du forum avec un role.")
    async def link_add(
        self,
        inter: ApplicationCommandInteraction,
        tag: str = commands.Param(description="Le tag du forum auquel lier un role."),
        role: str = commands.Param(
            description="Le role à lier au tag. Les rôles déjà liés à ce tag ne sont pas affichés."
        ),
    ):
        await inter.response.defer(ephemeral=True)

        # Link the role to the tag (either add it to the existing list of role for this tag, or create a new list)
        _tag = await self.tag_from_name(inter.guild, tag)
        _role = await self.role_from_name(inter.guild, role)

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

    @thread_link.sub_command(name="remove", description="Delier un tag du forum avec un role.")
    async def link_remove(
        self,
        inter: ApplicationCommandInteraction,
        tag: str = commands.Param(
            description="Le tag du forum duquel délier un role. Seuls les tags avec au moins un role lié sont affichés"
        ),
        role: str = commands.Param(
            description="Le role à lier au tag. Seuls les roles non liés à ce tag sont affichés."
        ),
    ):
        await inter.response.defer(ephemeral=True)

        # Retrieve the tag and role selected
        _tag = await self.tag_from_name(inter.guild, tag)
        _role = await self.role_from_name(inter.guild, role)

        if str(_tag.id) not in self.tag_role_map.keys():
            raise KeyError(f"Tag {tag} is not in database")

        # remove item and also remove tag if there is no role linked to it anymore
        roles = self.tag_role_map.get(str(_tag.id))
        if _role.id not in roles:
            raise ValueError(f"Role {_role.name} is not linked to tag {tag}")

        roles.remove(_role.id)
        if not roles:
            self.tag_role_map.pop(str(_tag.id))
        self.save_tag_role_map()

        # Send a confirmation message with all the roles linked to the tag

        linked_roles: List[disnake.Role] = (
            [inter.guild.get_role(id) for id in self.tag_role_map.get(str(_tag.id))] if roles else []
        )
        await inter.edit_original_message(
            embed=disnake.Embed(
                title=f"🧹 __**Tag**__ {_tag.emoji} {_tag.name}",
                color=disnake.Colour.green(),
                description=f"{_tag.emoji} **{_tag.name}** et **{_role.mention}** ne sont plus liés.",
            )
            .add_field(
                name="__Roles liés :__",
                value="\n> " + "\n> ".join([role.mention for role in linked_roles]) if roles else "*Aucun role lié*",
                inline=False,
            )
            .set_footer(text="Tu peux rejeter ce message pour le faire disparaitre.")
        )

    @thread_link.sub_command(name="view", description="Voir tous les roles liés à un tag")
    async def link_view(
        self,
        inter: ApplicationCommandInteraction,
        tag: str = commands.Param(description="Le tag à voir. Seuls les tags avec au moins un role lié sont affichés."),
    ):
        await inter.response.defer(ephemeral=True)

        _tag = await self.tag_from_name(inter.guild, tag)
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

    @thread_link.sub_command(name="view_all", description="Voir tous les tags et leurs roles liés")
    async def link_view_all(self, inter: ApplicationCommandInteraction):
        await inter.response.defer(ephemeral=True)

        embed = disnake.Embed(title="**ForumTag liés avec des roles :**", color=disnake.Colour.green()).set_footer(
            text="Tu peux rejeter ce message pour le faire disparaitre."
        )
        available_tags = (await inter.guild.fetch_channel(self.forum_channel_id)).available_tags
        for tag_str, role_ids in self.tag_role_map.items():
            embed.add_field(
                name=next((f"{tag.emoji} {tag.name}" for tag in available_tags if str(tag.id) == tag_str), ""),
                value="> " + "\n> ".join([role.name for role in inter.guild.roles if role.id in role_ids]),
            )

        await inter.edit_original_message(embed=embed)

    @commands.slash_command(
        name="thread", default_member_permissions=disnake.Permissions.all(), guild_ids=[int(os.getenv("BEP_SERVER"))]
    )
    async def thread(self, inter: ApplicationCommandInteraction):
        pass

    @thread.sub_command(
        name="refresh", description="Actualise les membres d'un thread (ne fait qu'ajouter des membres)"
    )
    async def thread_refresh(
        self, inter: ApplicationCommandInteraction, thread: str = commands.Param(description="Le thread à actualiser")
    ):
        await inter.response.defer(ephemeral=True)

        _thread = await self.thread_from_name(inter.guild, thread)

        # Check all the member that should be in the thread but aren't
        members_to_add: List[disnake.Member] = []
        already_added_members_ids: List[int] = [
            member.id for member in await _thread.fetch_members()
        ]  # Need to do this becauseThreadMember and Member does not compare correctly for now
        for tag in _thread.applied_tags:
            role_ids: Union[List[int], None] = self.tag_role_map.get(str(tag.id), None)
            if role_ids:
                for role_id in role_ids:
                    role = _thread.guild.get_role(role_id)
                    if role:
                        [
                            members_to_add.append(member)
                            for member in role.members
                            if member.id not in already_added_members_ids
                            and member not in members_to_add
                            and member != _thread.owner
                        ]

        # If nobody to add, end here
        if not members_to_add:
            await inter.edit_original_message(
                embed=disnake.Embed(
                    title=f"Actualisation du thread ***{thread}***", description="*Aucun membre à ajouter*"
                )
            )
            return

        # Add selected members
        for member in members_to_add:
            await _thread.add_user(member)

        # Send notif
        notif = self.thread_to_notif(_thread)
        for member in members_to_add:
            await member.send(embed=notif[0], components=[notif[1]])

        await inter.edit_original_message(
            embed=disnake.Embed(
                title=f"Actualisation du thread ***{thread}***", description=f"{len(members_to_add)} membres ajoutés"
            )
        )

    ### Commands autocomplete ###

    @link_add.autocomplete("tag")
    async def link_add_tag_autocomplete(self, inter: ApplicationCommandInteraction, value: str):
        return [
            tag.name
            for tag in (await inter.guild.fetch_channel(self.forum_channel_id)).available_tags
            if tag.name.lower().startswith(value.lower())
        ]

    @link_add.autocomplete("role")
    async def link_add_role_autocomplete(self, inter: ApplicationCommandInteraction, value: str):
        tag_name = inter.filled_options.get("tag", "")
        if tag_name == "":
            return [inter.guild.roles]
        else:
            tag = await self.tag_from_name(inter.guild, tag_name)
            role_already_linked_ids = self.tag_role_map.get(str(tag.id), [])
            return [
                role.name
                for role in inter.guild.roles
                if (role.id not in role_already_linked_ids and role.name.lower().startswith(value.lower()))
            ]

    @link_remove.autocomplete("tag")
    async def tlink_remove_tag_autocomplete(self, inter: ApplicationCommandInteraction, value: str):
        return [
            tag.name
            for tag in (await inter.guild.fetch_channel(self.forum_channel_id)).available_tags
            if tag.name.lower().startswith(value.lower()) and str(tag.id) in self.tag_role_map.keys()
        ]

    @link_remove.autocomplete("role")
    async def link_remove_role_autocomplete(self, inter: ApplicationCommandInteraction, value: str):
        tag_name = inter.filled_options.get("tag", "")
        if tag_name == "":
            return [inter.guild.roles]
        else:
            tag = await self.tag_from_name(inter.guild, tag_name)
            role_already_linked_ids = self.tag_role_map.get(str(tag.id), [])
            return [
                role.name
                for role in inter.guild.roles
                if (role.id in role_already_linked_ids and role.name.lower().startswith(value.lower()))
            ]

    @link_view.autocomplete("tag")
    async def link_view_tag_autocomplete(self, inter: ApplicationCommandInteraction, value: str):
        return [
            tag.name
            for tag in (await inter.guild.fetch_channel(self.forum_channel_id)).available_tags
            if self.tag_role_map.get(str(tag.id)) and tag.name.lower().startswith(value.lower())
        ]

    @thread_refresh.autocomplete("thread")
    async def thread_refresh_thread_autocomplete(self, inter: ApplicationCommandInteraction, value: str):
        return [
            thread.name
            for thread in (await inter.guild.fetch_channel(self.forum_channel_id)).threads
            if thread.name.lower().startswith(value.lower())
        ]

    ### Event listeners ###

    @commands.Cog.listener("on_thread_create")  # Called each time a new thread is created
    async def thread_create(self, thread: disnake.Thread):

        if thread.guild.id == int(os.getenv("BEP_SERVER")):

            logging.debug(f"[Cog:{self.qualified_name}] [Thread:{thread.name}#{thread.id}] Creation event")

            # Ignore thread that are not created from the selected forum channel
            if thread.parent_id != self.forum_channel_id:
                logging.debug(
                    f"[Cog:{self.qualified_name}] [Thread:{thread.name}#{thread.id}] ignored because not in selected forum channel"
                )
                return

            # Make a list of all the members that has at least one role corresponding to the tags of the thread, without duplicat
            members_to_add: List[disnake.Member] = []
            for tag in thread.applied_tags:
                role_ids: Union[List[int], None] = self.tag_role_map.get(str(tag.id), None)
                if role_ids:
                    for role_id in role_ids:
                        role = thread.guild.get_role(role_id)
                        if role:
                            [
                                members_to_add.append(member)
                                for member in role.members
                                if member not in members_to_add and member != thread.owner
                            ]

            # End here if nobody to add
            if not members_to_add:
                logging.debug(f"[Cog:{self.qualified_name}] [Thread:{thread.name}#{thread.id}] Nobody to add")
                return

            # Add all selected memner to the thread
            for member in members_to_add:
                await thread.add_user(member)

            # Send the notif to all selected members
            notif = self.thread_to_notif(thread)
            for member in members_to_add:
                await member.send(embed=notif[0], components=[notif[1]])

            logging.debug(
                f"[Cog:{self.qualified_name}] [Thread:{thread.name}#{thread.id}] {len(members_to_add)} member added"
            )

    @commands.Cog.listener("on_thread_update")
    async def thread_update(self, before: disnake.Thread, after: disnake.Thread):

        if after.guild.id == int(os.getenv("BEP_SERVER")):

            logging.debug(f"[Cog:{self.qualified_name}] [Thread:{after.name}#{after.id}] Update event")

            # Ignore thread that are not created from the selected forum channel
            if before.parent_id != self.forum_channel_id:
                logging.debug(
                    f"[Cog:{self.qualified_name}] [Thread:{after.name}#{after.id}] ignored because not in selected forum channel"
                )
                return

            new_tags: List[disnake.ForumTag] = [tag for tag in after.applied_tags if tag not in before.applied_tags]

            if not new_tags:
                logging.debug(f"[Cog:{self.qualified_name}] [Thread:{after.name}#{after.id}] Not new tags")
                return

            # Make a list of all the members that has at least on role corresponding to the new tags of the thread, without duplicat
            members_to_add: List[disnake.Member] = []
            members_already_added_ids: List[int] = [
                member.id for member in await before.fetch_members()
            ]  # Need to do this becauseThreadMember and Member does not compare correctly for now
            for tag in new_tags:
                role_ids: Union[List[int], None] = self.tag_role_map.get(str(tag.id), None)
                if role_ids:
                    for role_id in role_ids:
                        role = after.guild.get_role(role_id)
                        if role:
                            [
                                members_to_add.append(member)
                                for member in role.members
                                if member not in members_to_add and member.id not in members_already_added_ids
                            ]

            # End here if nobody to add
            if not members_to_add:
                logging.debug(f"[Cog:{self.qualified_name}] [Thread:{after.name}#{after.id}] Nobody new to add")
                return

            # Add all selected member to the thread
            for member in members_to_add:
                await after.add_user(member)

            # Send the notif to all selected members
            notif = self.thread_to_notif(after)
            for member in members_to_add:
                await member.send(embed=notif[0], components=[notif[1]])

            logging.debug(
                f"[Cog:{self.qualified_name}] [Thread:{after.name}#{after.id}] {len(members_to_add)} new member added"
            )


def setup(bot: commands.InteractionBot):
    bot.add_cog(Thread(bot))
