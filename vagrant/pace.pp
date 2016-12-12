class pace {

  package { "g++":
    ensure => present,
  }
  package { "git":
    ensure => present,
  }
  package { "python3":
    ensure => present,
  }

  # used for creating a PuTTy-compatible key file
  package { "putty-tools":
    ensure => present,
  }

}

include pace
