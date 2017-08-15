# Item Catalog Project

This is the Item Catalog project for Udacity's Fullstack Nanodegree

## How to use it:

Firstly, you will need a Google account to sign up/in.

You first must install both Virtual Box and Vagrant, which will run off of Virtual Box.

**Be sure to install Virtual Box first.**

## Inital Setup

[Virtual Box](https://www.virtualbox.org/wiki/Downloads) [Vagrant](https://www.vagrantup.com/downloads.html)

Once both of those are installed you must download Udacity's Vagrant environment available [here](https://github.com/udacity/fullstack-nanodegree-vm).

## Next steps

Clone this repo to your vagrant environment in a new folder named "item_catalog"

Once those have been downloaded, you must install the virtual environment. To install the environment go to the location in your **terminal** where you extracted/cloned the Udacity folder and type `vagrant up` inside of a terminal.

**Ensure that you are inside of the "vagrant" folder before running the command above**

At this point, the vagrant environment will install. This takes a while so go grab a cup of coffee or a beer and come back in approximately 10 minutes.

## Next steps

This vagrant environment will already have an empty "catalog" folder, which you can simply replace with the once provided on this repository.

Once all the requisite items are setup, you can run the virtual environment by running `vagrant ssh`

The virtual environment will now be live, congratulations!

Now type `cd /vagrant/item_catalog` to enter the project folder.

From here, simply type `python application.py` and the script will load up at the site `http://localhost:8000`.

Enjoy!
