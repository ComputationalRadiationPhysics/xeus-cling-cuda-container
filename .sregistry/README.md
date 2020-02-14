# Before the first push

Before you can push the image to the sregistry the first time, you have to setup some keys for signing images and logging in.

1. setup key with `singularity key newpair`
2. generate a key API at https://cloud.sylabs.io/keystore (30 days valid?) and store it at `~/.singularity/sylabs-token`

# Build and push

```bash
# create the recipes and build the containers
python build.py <config.json>
# push the containers to the registry
python push.py
```

Use `python recipe.py <config.py>` to create only a container recipe without building the container.
