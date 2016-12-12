class pace {

  package { "g++":
    ensure => present,
  }
  package { "mercurial":
    ensure => present,
  }
  package { "python3":
    ensure => present,
  }
  package { "python3-pip":
    ensure => present,
  }

  # used for creating a PuTTy-compatible key file
  package { "putty-tools":
    ensure => present,
  }

  exec { 'pip3 install pace':
    command => '/usr/bin/pip3 install -e hg+https://bitbucket.org/uyar/pace#egg=pace'
  }

}

include pace
