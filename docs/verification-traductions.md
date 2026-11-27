# Vérification des traductions — suivi de la phase 1

Objectif : texte complet, français lisible, absence de passages non traduits et de résidus techniques. La vérification approfondie de la fidélité viendra ensuite. Un contrôle automatique ou une correction ponctuelle ne vaut pas validation complète d’un numéro.

## Périmètre et sources

- 1 950 fichiers : numéros 0600–0649 et 1200–3099, dans `src/content/chapitres`.
- Originaux : `\\192.168.1.150\Media\Livres\EBOOK\Perry Rhodan Sammelband` ; accès confirmé le 27 novembre 2026.
- Les EPUB individuels 3055 et 3077 ne figurent pas dans l’inventaire initial de ce dossier ; rechercher d’autres exemplaires avant de conclure à une source absente.
- Attention : dans le recueil 2600–2699, le fichier interne `Band2269.html` correspond au roman 2669. Ne pas déduire les correspondances uniquement des noms internes.

## Corrections ciblées vérifiées sur l’original

Les passages corrigés seulement, pas les numéros entiers : 2547, 2586, 2599, 2668, 2669, 2701, 2737, 2759, 2848, 2871, 2874, 2887, 2908, 2909, 2936, 2962, 2983, 3008. Dans les numéros 2737 et 2871, des phrases supplémentaires absentes ont été rétablies après examen du contexte source.

Les résidus allemands courts suivants ont été corrigés par lecture du contexte français : 1401, 1608, 1710, 1738, 1789, 1801, 1813, 1831, 1842, 1932, 1933. Ils ne constituent pas une validation des romans.

## Anomalies encore à traiter

- Recherche du 27 novembre : 51 numéros contenaient des formulations de consignes de correction ou de réponse précédente. Ce résultat est antérieur à la correction ponctuelle du 2586 et inclut différentes formulations ; dédoublonner et examiner chaque occurrence dans son contexte original. Ne pas supprimer les consignes en masse sans rechercher les omissions associées.
- Les recherches de débuts de ligne allemands révèlent d’autres titres, phrases et fragments encore présents. Les noms propres, titres d’œuvres et termes fictifs exigent un tri contextuel.
- Établir la correspondance de chaque roman avec son EPUB, puis vérifier la structure et les portions de texte ; les rapports automatiques de taille, titres ou langue sont des indices, pas une preuve d’intégralité.
- Aucun des 1 950 numéros n’est encore attesté comme entièrement revu dans cette phase. Les corrections ci-dessus forment un premier lot ponctuel, et non une validation complète des romans concernés.

## Contrôles effectués

Les variantes explicites de marqueurs entre crochets ont été recherchées dans l’ensemble des fichiers ; de nouveaux types de marqueurs et consignes ont ensuite été trouvés. `git diff --check` a réussi après les corrections de ce lot. Les originaux et les fichiers préexistants non suivis doivent être préservés.
