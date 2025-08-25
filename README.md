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
   docker build -t ghcr.io/kaiserdrake/optcg-scraper .
   ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- USAGE EXAMPLES -->
## Usage

### As dockerized webservice

Run the container. You need to do two important things here:
 * `-p 38080:8080`: This maps port 38080 on your local machine to port 8080 inside the container, so you can access the web service.
 * `-v "$(pwd)/output:/tmp"`: It creates a directory mapping current folder and links it to the /tmp directory inside the container. This allows you to access the CSV files or downloaded images that the scraper saves.

```sh
docker run -p 38080:8080 -v "$(pwd)/output:/tmp" --name optcg-api ghcr.io/kaiserdrake/optcg-scraper
```

Your web service is now running! You can access it from your web browser or a tool like curl.

List all packs (JSON):
```sh
curl http://localhost:38080/packs?format=json
```

Get cards for a specific pack (OP-01):

```sh
curl http://localhost:38080/cards/556101?format=json
```
Trigger the "scrape all" process:
This will start the long-running process of scraping all cards. The files will appear in the output/cards or output/downloaded_images directory on your local machine.

```sh
curl http://localhost:38080/packs/all?format=csv
```


### Locally

The project is now as a package (app), you should run the scraper as a module from the root directory of the project.
Use the `python -m` flag.

For example, to list all packs:
```sh
python -m app.scraper packs
```
To list all cards in a specific pack:
```sh
python -m app.scraper cards <series_id>
```


<!-- LICENSE -->
## License

Distributed under the project_license. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

