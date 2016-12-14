class pace {

  exec { 'pip3 install pace':
    command => '/usr/bin/pip3 install -e hg+https://bitbucket.org/uyar/pace#egg=pace'
  }

}

include pace
