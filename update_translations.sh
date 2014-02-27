cd survey
../manage.py makemessages -l es
../manage.py makemessages -l pt
../manage.py makemessages -l fr
../manage.py makemessages -l ht
../manage.py makemessages -l vi
../manage.py makemessages -l km
../manage.py makemessages -l zh
../manage.py makemessages -l ar
find -name *.po -exec sed -i 's/\\u003c/</g' {} \;
find -name *.po -exec sed -i 's/\\u003e/>/g' {} \;
cd ..
./manutranslate.py
./autotranslate.py
cd survey
../manage.py compilemessages
