class base {

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
  package { "python3-dev":
    ensure => present,
  }
  package { "libyaml-dev":
    ensure => present,
  }
  package { "fakechroot":
    ensure => present,
  }

  # used for creating a PuTTy-compatible key file
  package { "putty-tools":
    ensure => present,
  }

}

include base
