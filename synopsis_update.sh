#!/bin/sh
# Usage: /bin/sh synopsis_update.sh > docs/synopsis.md
# Note: Important to use /bin/sh and not bash for the \n to be rendered properly
# Otherwise, maybe need "echo -e" with bash

set -e

echo "# Synopsis\n"
echo "A list of all commands and options with isitfit\n\n"
echo "---\n\n"


showHelp() {
  command_1="$1"
  command_2="isitfit $command_1"
  echo "## \`$command_2 --help\`\n"
  echo "\`\`\`"
  isitfit --skip-check-upgrade $command_1 --help
  echo "\`\`\`\n\n"
}

showHelp ""
showHelp version
showHelp cost
showHelp "cost analyze"
showHelp "cost optimize"

showHelp tags
showHelp "tags dump"
showHelp "tags suggest"
showHelp "tags push"

# No need for this ATM since migrations are internally handled by isitfit and not by the end user
# These commands were added to help me manually debug/develop the migrations feature
# showHelp migrations
# showHelp "migrations show"
# showHelp "migrations migrate"
