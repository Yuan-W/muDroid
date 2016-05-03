echo "Setting up environment..."

APK_NAME="CleanCalculator" 
BASEDIR=$(dirname "$0")

cp $BASEDIR/$APK_NAME.apk $BASEDIR/../
if [ ! -d "$BASEDIR/../$APK_NAME" ]; then
  mkdir $BASEDIR/../$APK_NAME
fi
cp $BASEDIR/commands $BASEDIR/../$APK_NAME/
cp $BASEDIR/config $BASEDIR/../$APK_NAME/

echo "Done"
echo "Please type 'python mudroid.py $APK_NAME.apk' in the muDroid folder to start."