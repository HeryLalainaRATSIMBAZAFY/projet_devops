# Démonstration du cycle CI/CD

```
git push ──► GitHub ──webhook──► Jenkins ──► docker build ──► Nexus (registry privé)
                                    │                              │
                                    └──► docker compose up ◄── pull┘ ──► notification email
```

| Étape | Outil | Où c'est défini |
|---|---|---|
| 1. Push du code | GitHub `HeryLalainaRATSIMBAZAFY/projet_devops` | `git push` |
| 2. Déclenchement par webhook | GitHub Webhook → ngrok → Jenkins | `triggers { githubPush() }` du `Jenkinsfile` |
| 3. Build de l'image | Docker | stage `Build Docker Image` |
| 4. Push vers le registry privé | Nexus, dépôt `docker-hosted` (`localhost:8082`) | stage `Push to Nexus` |
| 5. Déploiement | Docker Compose (`docker-compose.yml`) | stages `Deploy with Docker Compose` + `Smoke test` |
| 6. Notification | Email Extension | bloc `post { success / failure }` |

## Services

| Service | URL | Identifiants |
|---|---|---|
| Application | http://localhost:5000 | — |
| Jenkins | http://localhost:8090 | compte créé à l'étape A |
| Nexus | http://localhost:8081 | `admin` / mot de passe dans `ci/.env.ci` (non versionné) |
| Registry Docker | `localhost:8082` | mêmes identifiants que Nexus |

## 0. Démarrer l'infrastructure (déjà fait une fois)

```bash
docker compose -f ci/docker-compose.ci.yml up -d --build
```

Sur une nouvelle machine seulement, configurer Nexus (registry Docker sur le port 8082) :

```bash
bash ci/nexus-setup.sh <mot_de_passe_admin_nexus>
```

## A. Initialiser Jenkins (une seule fois)

1. Ouvrir http://localhost:8090. Le mot de passe de déverrouillage s'obtient avec :
   ```bash
   docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
   ```
2. Choisir **Select plugins to install** → **None** (les plugins sont déjà inclus dans l'image), puis créer le compte admin.

## B. Identifiants dans Jenkins

*Manage Jenkins → Credentials → System → Global → Add Credentials*

- **Username with password** — ID `nexus-credentials`, utilisateur `admin`, mot de passe = `NEXUS_PASSWORD` de `ci/.env.ci`.
- (Uniquement si le dépôt GitHub est privé) **Username with password** — ID `github-credentials`, votre login GitHub + un *Personal Access Token*.

## C. Notification email

*Manage Jenkins → System*

- **Jenkins Location** → URL : `http://localhost:8090/`, email admin : votre adresse.
- **Extended E-mail Notification** → SMTP `smtp.gmail.com`, port `465`, *Use SSL*, credentials = votre adresse Gmail + un **mot de passe d'application** Google (Compte Google → Sécurité → Mots de passe des applications).
- Le destinataire se règle dans `NOTIFY_EMAIL` du `Jenkinsfile`.

## D. Créer le job

*New Item → nom `projet_devops` → Pipeline*

- **Triggers** : cocher *GitHub hook trigger for GITScm polling*.
- **Pipeline** : *Pipeline script from SCM* → *Git*
  - Repository URL : `https://github.com/HeryLalainaRATSIMBAZAFY/projet_devops.git`
  - Branch : `*/develop`
  - Script Path : `Jenkinsfile`
- Lancer un premier **Build Now** manuel pour vérifier que tout est vert.

## E. Webhook GitHub → Jenkins

GitHub ne peut pas joindre `localhost` : on expose Jenkins avec **ngrok**.

```bash
winget install ngrok.ngrok
```
```bash
ngrok config add-authtoken <token depuis dashboard.ngrok.com>
```
```bash
ngrok http 8090
```

Sur GitHub : *Settings → Webhooks → Add webhook*

- Payload URL : `https://<sous-domaine>.ngrok-free.app/github-webhook/` (avec le `/` final)
- Content type : `application/json`
- Événement : *Just the push event*

L'onglet *Recent Deliveries* doit afficher une réponse `200`.

## F. La démonstration

1. Modifier quelque chose de visible, par exemple le titre dans `templates/base.html`.
2. Pousser :
   ```bash
   git commit -am "demo: changement du titre" && git push
   ```
3. Montrer, dans l'ordre :
   - GitHub → *Webhooks → Recent Deliveries* : la requête envoyée à Jenkins ;
   - Jenkins : le build démarre seul (*Started by GitHub push*) et enchaîne les stages ;
   - Nexus → *Browse → docker-hosted* : la nouvelle image `projet_devops:<numéro de build>` ;
   - http://localhost:5000 : le changement est en ligne ;
   - la boîte mail : le message `SUCCESS - projet_devops #N`.
4. Optionnel : casser volontairement le build (erreur de syntaxe dans `Dockerfile`) pour montrer la notification `FAILED`.
