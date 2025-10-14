if [ -z $1 ]; then
    echo "Please provide a message for the revision"
    exit 1
fi

CURRENT_VERSION=`alembic current| cut -d ' ' -f 1`
if [ -z "$CURRENT_VERSION" ]; then
    echo "No current version found, starting from 0000"
    NEXT_VERSION="0000"
else
    NEXT_VERSION=`printf "%04d" $((10#$CURRENT_VERSION + 1))`
fi

MESSAGE="$*"
echo "Next version: $NEXT_VERSION"
echo "Message: $MESSAGE"
alembic revision --autogenerate --rev-id $NEXT_VERSION -m "$MESSAGE"