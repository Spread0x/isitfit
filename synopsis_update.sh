#!/bin/sh
# Usage: /bin/sh synopsis_update.sh > SYNOPSIS.md

set -e

echo "# SYNOPSIS for isitfit\n"

showHelp() {
  command_1="$1"
  command_2="isitfit $command_1"
  echo "## \`$command_2 --help\`\n"
  echo "\`\`\`"
  isitfit --skip-check-update $command_1 --help
  echo "\`\`\`\n\n"
}

showHelp ""
showHelp version
showHelp cost
showHelp "cost optimize"
showHelp "cost analyze"
showHelp tags
showHelp "tags dump"
showHelp "tags suggest"
showHelp "tags push"
