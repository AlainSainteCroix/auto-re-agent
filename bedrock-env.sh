# Config Bedrock pour re-agent — à sourcer avant un run.
#   cd /home/techalain/workspace/projects/labs/auto-re-agent && . .venv/bin/activate && . ./bedrock-env.sh
#
# Aucun secret ici : les identifiants AWS vivent dans ~/.aws (chaîne standard).
# Voir CLAUDE.md §7 (modèle imposé) et §9 (pas de secret dans le repo).
export RE_AGENT_BEDROCK=1
export RE_AGENT_BEDROCK_MODEL="us.anthropic.claude-opus-4-6-v1"   # le suffixe :0 est rejeté (400)
export AWS_REGION="us-east-1"
