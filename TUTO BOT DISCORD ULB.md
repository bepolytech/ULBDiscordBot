# Tutoriel sur comment mettre en place le bot Discord de vérification ULB sur votre serveur Discord

> Pour toute question ou aide: contactez le BEP et/ou leur·e(·s) délégué·e(·s) IT.

## 📨 Inviter le bot sur votre serveur

Le lien d'invitation doit être demandé à (TODO). Copiez-collez le lien dans votre navigateur. Dans le menu discord apparaissant, choissez le serveur auquel ajouter le bot, puis laissez coché les autorisations par default et cliquez sur `authoriser`. Pour ajouter plusieurs serveurs, répetez l'operation avec le même lien.



## ⚙ Configuration du serveur

### Role et permissions

Si pas encore fait, créez un role pour les membres vérifiés (ex: `@ULB`) et retirez les permissions de `@everyone` que vous ne voulez pas octoyer aux membres non vérifiés. Si vous voulez forcer les membres vérifiés à afficher leur vrai nom comme pseudo, retirez la permissions `changer son pseudo` au role `@ULB` et mettez le role du bot au dessus du role `@ULB` dans la liste des roles du serveur (idéalement, mettez le role du bot juste en dessous de celui des modérateurs).

### Setup

Maintenant que le serveur est correctement paramètré, vous pouvez utiliser `/setup` (nécessite d'avoir les permissions d'administrateur). Le premier paramètre (obligatoire) est le role `@ULB` à attribuer aux membres vérifiés. Le second paramètre permet de choisir si vous voulez forcer les membres vérifiés à afficher leur vrai nom comme pseudo (oui par défaut).

La réponse à cette commande devrait vous confirmer que le serveur est bien configuré. Dès lors, les membres déjà vérifiés du serveur devrait recevoir automatiquement le role `@ULB` (et eventuellement être renommer, en fonction de ce que vous avez choisit plus haut) et tout nouveau membre non vérifié recevront un message de notification à leur arrivée avec les instructions pour vérifier leur adresse email.

En cas de problème avec les permissions du role ou du bot, celui-ci vous avertira lors de cette commande, et vous pouvez toujours utiliser `/info` pour voir la configuration actuelle du serveur et l'état des permissions.

## FAQ

* Est-ce que je peux ajouter manuellement un membre sans qu'il doivent vérifier sont email ?

> Vous pouvez ajouter des membres au role `@ULB`, ceux-ci ne seront jamais retirés par le bot *(néanmoins ils ne seront pas considérés comme utilisateurs vérifiés sur les autres serveurs du bot)*.

* Qu'est-ce qu'il se passe si le bot est offline et que des nouveaux membres arrivent ?

> Si le bot est offline (en cas de panne) et que des nouveaux membres déjà vérifiés arivent sur votre serveur, ceux-ci seront validés dés que le bot repasse online, mais vous pouvez toujours les ajouter manuellement au role `@ULB` en attendant si nécessaire.

* Le nom que le bot a utiliser comme pseudo contient aussi les deuxièmes prenoms et/ou nom de famille.

> Le pseudo d'un utilisateur vérifié est généré à partir de l'adresse email. Si l'utilisateur à plusieurs nom et/ou prénom, ils sont tous utilisés pour générer son pseudo *(ex: `pierre.théodore.verhaegen@ulb.be` -> `Pierre Théodore Verhaegen`)*. Si l'utilisateur ne veut afficher que son prénom principal, il faudra envoyer un message à (TODO).

* Mon serveur est paramètré pour forcer renommer les membres vérifiés avec leur vrai nom mais certains membres ne sont pas renommés.

> Le bot ne peux renommer que les membres dont le role le plus élevé est en dessous de celui du bot dans la list des roles du serveur. Idéalement, mettez le role du bot juste en dessous de celui des modérateurs pour s'assurer que le bot puisse renommer tous les autres membres du serveur (et demandez à vos modo de se renommer eux-mêmes si nécessaire).
