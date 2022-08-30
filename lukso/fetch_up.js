const Web3 = require('web3');
const { ERC725 } = require('@erc725/erc725.js');
require('isomorphic-fetch');
const conf = require('./config.json');

const PROFILE_ADDRESS = process.argv[2];

const erc725schema = require('@erc725/erc725.js/schemas/LSP3UniversalProfileMetadata.json');
const provider = new Web3.providers.HttpProvider(conf.rpc_endpoint);
const config = { ipfsGateway: conf.ipfs_gateway };

async function fetchProfile(address) {
    try {
        const profile = new ERC725(erc725schema, address, provider, config);
        return await profile.fetchData();
    } catch (error) {
        return console.log('This is not an ERC725 Contract');
    }
}

async function fetchProfileData(address) {
    try {
        const profile = new ERC725(erc725schema, address, provider, config);
        return await profile.fetchData('LSP3Profile');
    } catch (error) {
        return console.log('This is not an ERC725 Contract');
    }
}

fetchProfile(PROFILE_ADDRESS).then((profileData) =>
    console.log(JSON.stringify(profileData, undefined, 2)),
);

fetchProfileData(PROFILE_ADDRESS).then((profileData) =>
    console.log(JSON.stringify(profileData, undefined, 2)),
);
