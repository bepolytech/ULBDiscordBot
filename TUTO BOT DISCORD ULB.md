# Tutoriel sur comment mettre en place le bot Discord de vérification ULB sur votre serveur Discord
> Pour toute question ou aide: contactez le BEP et/ou leur·e(·s) délégué·e(·s) IT.

## Conditions
Ce bot requiert:  
- Un serveur Discord configuré un minimum:  
    Un rôle "ULB" (ou "étudiant", ou nommé autrement à votre choix) avec les permissions qui vont conviennent.  
- ~20 minutes si tout se passe bien.


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

## 2. Bot

// TODO
### 2.1 Ajout du bot dans le serveur

// TODO

[insérer screenshot invitation bot dans serveur]

// TODO

### 2.2 Setup du bot dans le serveur

// TODO

## 3. Détails:
- Une fois vérifiée sur un serveur, une personne aura alors son compte Discord vérifié sur tous les serveurs Discord d'associations de l'ULB utilisant aussi ce bot ULB.  
Ce bot sert vraiment d'authentification inter-serveurs: `Compte Discord <-> Email ULB`  
- Une adresse email ULB ne peut être vérifiée que pour un seul compte Discord. Il n'est donc possible d'utiliser une même adresse ULB que pour un seule persone.

// TODO

## 4. FaQ
- Est-ce que des gens sans adresse mail ULB peuvent quand-même avoir accès au rôle?  
```Bien sûr! Le rôle présent sur votre serveur dépend de vous, vous pouvez donc ajouter manuellement des personnes sans adresse mail ULB. Cependant, il.elle.s ne seront pas ajouter dans la vérification automatique inter-serveur Discord ULB.```  
- Eefse  
```sedvzreg```

// TODO

Bisous, le BEP <3  
[insérer logo BEP]

_by Oscar Van Slijpe & Lucas Placentino_