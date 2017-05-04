class clioc {

  exec { 'pip3 install clioc':
    command => '/usr/bin/pip3 install -U clioc'
  }

}

include clioc
