export PYTHONPATH=$PYTHONPATH:./google_appengine
nosetests --with-gae --without-sandbox --nologcapture muninn/tests
