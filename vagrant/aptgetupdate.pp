class aptgetupdate {

  # This apt-get update below is meant to ward
  # off "Unable to fetch some archives, maybe run apt-get update or try with --fix-missing?"
  # errors.
  exec { 'apt-get update':
    command => '/usr/bin/apt-get update'
  }

}

include aptgetupdate
