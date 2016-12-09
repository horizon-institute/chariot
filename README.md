## Running

First, [install docker compose](https://docs.docker.com/compose/install/).
Then, in the chariot directory run:

	./start.sh

This script will ask if you want any domains on https, and will get certificates for them before starting up the server.
It will take some time to start up first time. But, when it is finished CharIoT will be running.

The first time you open CharIoT in a browser, it will ask you to create an admin user for the system.

## Testing

Install [node.js](https://nodejs.org/en/download/package-manager/). To setup the test scripts, run:

	npm install
	
Then to run the script use:

	npm run fakeData