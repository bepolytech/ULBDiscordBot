# Tutoriel sur comment mettre en place le bot Discord de vérification ULB sur votre serveur Discord
> Pour toute question urgente ou aide urgente: contactez le BEP et/ou leur·e(·s) délégué·e(·s) IT.

Le setup du bot sur votre serveur prendra ~10 minutes si tout se passe bien.  
<!--
## 1. Serveur Discord
Créez votre serveur Discord.  
Mettez des administrateurs et/ou modérateurs, de votre association.  

### 1.1 Rôle ULB  
Créez un rôle qui sera appliqué aux personnes vérifiées comme ayant bien une adresse email ULB. Par exemple "ULB", ou "étudiant ULB" ou ce que vous préférez d'autre.  
Mettez à ce rôle les permissions qui vous arrangent. Par exemple: droit d'écrire, de réagir, etc.  

[insérer screenshot exemple role]

>Si vous choisssez de laisser le bot renommer les pseudos serveur des personnes, automatiquement depuis leur adresse mail @ulb.be:  
>Nous vous conseillons d'enlever le droit de changer son pseudo serveur pour tout les rôles. Ceci fixera leur nom réel et ils ne pourront pas le changer. (Les administrateurs et autre rôles ayant droit de renommer les autres ont toujours le droit de les renommer manuellement si besoin)

### 1.2 Hiérarchie des rôles
Le rôle du bot (normalement qui a le même nom que le bot) doit **impérativement** être placé hiérarchiquement au-dessus des rôles dont il devra ajouter et renommer. (Pour ne pas vous compliquer la vie, vous pouvez le mettre tout en haut.)  

[insérer screenshot hierarchie role discord]
-->

## 📨 1. Inviter le bot sur votre serveur

Le lien d'invitation doit être demandé à (TODO, au BEP/aux délégués IT du BEP). Copiez-collez le lien dans votre navigateur. Dans le menu discord apparaissant, choissez le serveur auquel ajouter le bot, puis laissez coché les autorisations par default et cliquez sur `authoriser`. Pour ajouter plusieurs serveurs, répetez l'operation avec le même lien.



## ⚙ 2. Configuration du serveur

### 2.1 Role et permissions

Si pas encore fait, créez un role pour les membres vérifiés (ex: `@ULB`, `@EtudiantULB`, ou autre) et retirez les permissions de `@everyone` que vous ne voulez pas octoyer aux membres non vérifiés. Si vous voulez forcer les membres vérifiés à afficher leur vrai nom comme pseudo, retirez la permissions `changer son pseudo` au role `@ULB` **et mettez le role du bot au dessus du role `@ULB` dans la liste des roles du serveur** (idéalement, mettez le role du bot juste en dessous de celui des modérateurs).

### 2.2 Setup

Maintenant que le serveur est correctement paramètré, vous pouvez utiliser `/setup` (nécessite d'avoir les permissions d'administrateur). Le premier paramètre (obligatoire) est le role `@ULB` à attribuer aux membres vérifiés. Le second paramètre permet de choisir si vous voulez forcer les membres vérifiés à afficher leur vrai nom comme pseudo (oui par défaut).

La réponse à cette commande devrait vous confirmer que le serveur est bien configuré. Dès lors, les membres _déjà vérifiés_ du serveur devrait recevoir automatiquement le role `@ULB` (et eventuellement être renommés, en fonction de ce que vous avez choisit plus haut) et tout nouveau membre non vérifié recevront un message de notification à leur arrivée avec les instructions pour vérifier leur adresse email.

En cas de problème avec les permissions du role ou du bot, celui-ci vous avertira lors de cette commande, et vous pouvez toujours utiliser `/info` pour voir la configuration actuelle du serveur et l'état des permissions.

## 🛑 3. Administration
Pour ajouter manuellement, supprimer ou modifier un utilisateur, les commandes `/user add`, `/user delete` et `/user edit` doivent être effectuées dans le serveur spécial d'administration du bot. Ce serveur est réservé aux responsables du bot, si vous voulez effectuer une de ces commandes manuelles, contactez le BEP et/ou ses délégués IT. Nous pouvons également vous rajouter sur le serveur la personne responsable de votre association étudiante, sur accord et appréciation du BEP.  

## 🧩 4. Détails
* Une fois vérifiée sur un serveur, une personne aura alors son compte Discord vérifié sur tous les serveurs Discord d'associations de l'ULB utilisant aussi ce bot ULB.  
Ce bot sert vraiment d'authentification inter-serveurs: `Compte Discord <-> Email ULB`

* Une adresse email ULB ne peut être vérifiée que pour un seul compte Discord. Il n'est donc possible d'utiliser une même adresse ULB que pour un seule persone.

## ❓ 5. FAQ

* Est-ce que je peux ajouter manuellement un membre sans qu'il doivent vérifier sont email ?

> Vous pouvez ajouter des membres au role `@ULB`, ceux-ci ne seront jamais retirés par le bot *(néanmoins ils ne seront pas considérés comme utilisateurs vérifiés sur les autres serveurs où se trouve le bot)*.

* Qu'est-ce qu'il se passe si le bot est offline et que des nouveaux membres arrivent ?

> Si le bot est offline (en cas de panne) et que des nouveaux membres déjà vérifiés arivent sur votre serveur, ceux-ci seront validés dés que le bot repasse online, mais vous pouvez toujours les ajouter manuellement au role `@ULB` en attendant si nécessaire.

* Le nom que le bot a utiliser comme pseudo contient aussi les deuxièmes prenoms et/ou nom de famille.

> Le pseudo d'un utilisateur vérifié est généré à partir de l'adresse email. Si l'utilisateur à plusieurs nom et/ou prénom, ils sont tous utilisés pour générer son pseudo *(ex: `pierre.théodore.verhaegen@ulb.be` -> `Pierre Théodore Verhaegen`)*. Si l'utilisateur ne veut afficher que son prénom principal, il faudra envoyer un message à votre/vos modérateur(s) et à (TODO, délégués IT du BEP).

* Mon serveur est paramètré pour forcer renommer les membres vérifiés avec leur vrai nom mais certains membres ne sont pas renommés.

> Le bot ne peut renommer que les membres dont le role le plus élevé est en dessous de celui du bot dans la liste des roles du serveur. Idéalement, mettez le role du bot juste en dessous de celui des modérateurs pour s'assurer que le bot puisse renommer tous les autres membres du serveur (et demandez à vos modo de se renommer eux-mêmes si nécessaire).

--------------------------------

**Bisous, le BEP. <3**  

<img style="background-color:white;padding:10px" height="80" src="https://user-images.githubusercontent.com/23436953/194563884-413e8ab8-aaa5-4f0b-a19a-c3b3f809e884.png">  

_by Oscar Van Slijpe & Lucas Placentino_
