priv_reg=10.20.193.214:5000

docker build . -t ${priv_reg}/mbam/freesurfer-recon:latest
docker push ${priv_reg}/mbam/freesurfer-recon:latest



