# Numerical-Data-Handler
- Use your own Polygon API Key
  - Make a file called polygon_api_key at the root of the project
  - Just have the key at the first line of the file
- The keys for pulling from the bucket are provided for you
- You will also need Cloudflare R2 keys to push
  - Contact me if you do not have them

## Dependencies
### If you are planning on just downloading from R2 run this
```bash
pip install -r download_from_r2_requirements.txt
```
### If you are working on the upload script (probably no need to do this, as the scripts are fully functional)
```bash
pip install -r dev_requirements.txt
```
## Usage
- The loading of data to R2 is already automated, do not attempt to run load_next_month_to_r2.py unless you're Ryan or myself
- An example of downloading the data is in `pull_data_from_r2_example.ipynb`