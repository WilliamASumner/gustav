# NAFC HTML
## Credit
This guide was inspired by [this tutorial](https://tecadmin.net/install-apache-mod-wsgi-on-ubuntu-18-04-bionic/).

## Apache Installation

1. Make sure apache is installed with:
```
sudo apt-get update
sudo apt-get install apache2 apache2-utils
```

2. Make sure python3 is installed with:
```
sudo apt-get install python3-pip
```

<del>
3. Install the mod\_wsgi Apache module:
```
~~sudo apt-get install libapache2-mod-wsgi~~
```
</del>  
Note: Using the distro-provided version of mod\_wsgi is not recommended. [It should be installed from source instead](https://modwsgi.readthedocs.io/en/develop/installation.html).

4. Restart the apache server for changes to take effect
```
sudo apachectl restart
```

## Apache Configuration
1. Copy `wsgi_test_script.py` to `/var/www/wsgi/`, or wherever you intend to install WSGI scripts. This directory must match the directory in the step below.
2. Add the line below to the file `/etc/apache2/conf-available/mod-wsgi.conf`
```
WSGIScriptAlias /ALIAS_NAME /var/www/wsgi/wsgi_test_script.py
```

3. Enable the new configuration and then restart Apache with:
```
sudo a2enconf mod-wsgi
sudo apachectl restart
```

4. The URL `http://YOUR_SITE/ALIAS_NAME` should now show the following output: 
<h1>This is the homepage!</h1>  

and the following output for `http://YOUR_SITE/ALIAS_NAME/test`:
<h1>This is the test page!</h1>

## Errors
If the site returns an *Interal Server Error* or a 404, check the output in `/var/log/apache2/error.log`.  
There are a couple common errors:
### Incorrect response value type
*The output:*
```
TypeError: sequence of byte string values expected, value of type str found
```
*The cause:*
This error is sneaky because a python 2.7 installation won't complain about a response function returning a string delimited by quotes (''/""), but python 3 will, because regular strings are no longer a byte string type. To fix this, use either a `b'YOUR\_STRING\_HERE'` in python 3 code, or just stick to `b"YOUR_STRING_HERE"` for interoperability. See `homepage_handler` and `test_handler` in `wsgi_test_script.py`.

### Missing WSGI application
*The output:*
```
Target WSGI script '/var/www/wsgi/wsgi_test_script.py' does not contain WSGI application 'application'
```
*The cause:*
In order for mod\_wsgi to properly instantiate the app, it needs to find either a function, class or object with the name 'application' to run. To fix this, make sure you have one of the three in your wsgi script. See `wsgi_test_script.py` for an example.
