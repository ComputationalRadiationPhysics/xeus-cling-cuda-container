# Before the first push

Before you can push the image to the sregistry the first time, you have to setup some keys for signing images and logging in.

1. setup key with `singularity key newpair`
2. generate a key API at https://cloud.sylabs.io/keystore (30 days valid?) and store it at `~/.singularity/sylabs-token`
