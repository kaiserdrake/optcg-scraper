<!-- GETTING STARTED -->
## Getting Started

To get a local copy up and running follow these simple example steps.


### Build using Docker

1. Clone the repo
   ```sh
   git clone git@github.com:kaiserdrake/optcg-scraper.git
   ```
2. Enter to the project directory such that Dockerfile is present in the current directory
   ```sh
   cd optcg-scraper
   ```
2. Build the docker image
   ```sh
   docker build -t optcg-scraper .
   ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- USAGE EXAMPLES -->
## Usage

To get the list of packs and their corresponding series_id, you can execute the following command:
```sh
docker run optcg-scraper packs
```
Alternatively, you can specify the output format as JSON:
```sh
docker run optcg-scraper packs --format json
```

For packs, the supported output formats are `text`, `csv` and `json`.

To get the list of cards in a specific pack, you can execute the following command:
```sh
docker run optcg-scraper cards <series_id>
```
Similarly, you can specify the output format as JSON:
```sh
docker run optcg-scraper cards <series_id> --format json
```
For cards, supported output formats are `text`, `csv`, `json` and `img`.
When `img` format is specified, the images of the cards will be downloaded to
the `downloaded_images` directory.
But since we are using Docker, the directory must be mounted as follows:
```sh
docker run -v $(pwd)/downloaded_images:/tmp/downloaded_images optcg-scraper cards <series_id> --format img
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- LICENSE -->
## License

Distributed under the project_license. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

