// Pipeline CI/CD : GitHub (webhook) -> Jenkins -> build Docker -> Nexus -> Docker Compose -> notification
// Jenkins tourne dans un conteneur Linux (voir ci/docker-compose.ci.yml), d'où l'usage de `sh`.
pipeline {
    agent any

    // 2- Déclenchement automatique par le webhook GitHub (POST /github-webhook/)
    triggers {
        githubPush()
    }

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    environment {
        // Registry privé Nexus (dépôt "docker-hosted", connecteur HTTP 8082).
        // "localhost" est vu par le démon Docker de l'hôte : pas besoin de "insecure-registries".
        REGISTRY     = 'localhost:8082'
        IMAGE_NAME   = 'projet_devops'
        IMAGE_TAG    = "${env.BUILD_NUMBER}"
        NOTIFY_EMAIL = 'lalainatag@gmail.com'   // destinataire de la notification
    }

    stages {

        // 1- Le code poussé sur GitHub est récupéré (job "Pipeline script from SCM")
        stage('Checkout') {
            steps {
                checkout scm
                sh 'git log -1 --pretty="Commit %h par %an : %s"'
            }
        }

        // 3- Build de l'image Docker
        stage('Build Docker Image') {
            steps {
                sh '''
                    docker build -t $REGISTRY/$IMAGE_NAME:$IMAGE_TAG .
                    docker tag $REGISTRY/$IMAGE_NAME:$IMAGE_TAG $REGISTRY/$IMAGE_NAME:latest
                '''
            }
        }

        // 4- Push vers le registry privé Nexus
        stage('Push to Nexus') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'nexus-credentials',
                    usernameVariable: 'NEXUS_USER',
                    passwordVariable: 'NEXUS_PASS'
                )]) {
                    sh '''
                        echo "$NEXUS_PASS" | docker login $REGISTRY -u "$NEXUS_USER" --password-stdin
                        docker push $REGISTRY/$IMAGE_NAME:$IMAGE_TAG
                        docker push $REGISTRY/$IMAGE_NAME:latest
                    '''
                }
            }
        }

        // 5- Déploiement automatique avec Docker Compose (image tirée depuis Nexus)
        stage('Deploy with Docker Compose') {
            steps {
                sh '''
                    docker compose pull web
                    docker compose up -d --no-build --remove-orphans
                    docker compose ps
                '''
            }
        }

        stage('Smoke test') {
            steps {
                sh '''
                    for i in $(seq 1 20); do
                        if curl -fsS -o /dev/null http://host.docker.internal:5000/; then
                            echo "Application disponible sur http://localhost:5000"; exit 0
                        fi
                        sleep 3
                    done
                    echo "L'application ne répond pas"; docker compose logs --tail=50 web; exit 1
                '''
            }
        }
    }

    // 6- Notification de fin de pipeline
    post {
        success {
            echo "Pipeline réussi : image $REGISTRY/$IMAGE_NAME:$IMAGE_TAG déployée"
            emailext(
                to: "${NOTIFY_EMAIL}",
                subject: "SUCCESS - ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                body: """Pipeline réussi.
Image : ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}
Application : http://localhost:5000
Détails : ${env.BUILD_URL}"""
            )
        }
        failure {
            echo 'Pipeline échoué'
            emailext(
                to: "${NOTIFY_EMAIL}",
                subject: "FAILED - ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                body: """Pipeline échoué.
Logs : ${env.BUILD_URL}console"""
            )
        }
        always {
            sh "docker logout $REGISTRY || true"
        }
    }
}
