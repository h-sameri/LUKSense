const conf = require('./config.json');
const Web3 = require('web3');
const web3 = new Web3();
const myEOA = web3.eth.accounts.privateKeyToAccount(conf.private_key);
const { LSPFactory, LSP4DigitalAssetMetadata, LSP4Metadata } = require('@lukso/lsp-factory.js');
const lspFactory = new LSPFactory(conf.rpc_endpoint, {
  deployKey: conf.private_key,
  chainId: 2828,
  ipfsGateway: conf.ipfs_gateway
});
var name = 'LUKSense NFT';
var symbol = 'LUT';
var description = 'NFT 2.0 created with LUKSense platform';
var url = 'https://lukso.network/';
var creator = myEOA.address;
process.argv.forEach(function (val, index, array) {
  if (val.startsWith("name=")){
    name = val.split('=')[1];
  } else if (val.startsWith("symbol=")){
    symbol = val.split('=')[1];
  } else if (val.startsWith("description=")){
    description = val.split('=')[1];
  } else if (val.startsWith("url=")){
    url = val.split('=')[1];
  } else if (val.startsWith("creator=")){
    creator = val.split('=')[1];
  }
});
LSP4DigitalAssetMetadata.uploadMetadata({
        LSP4Metadata: {
          description: description,
          links: [{
            title: name,
            url: url
          }]
        }
}).then(metaData => lspFactory.LSP7DigitalAsset.deploy({
    isNFT: true,
    controllerAddress: myEOA.address,
    name: name,
    symbol: symbol,
    creators: [creator],
    digitalAssetMetadata: metaData
}, {
  onDeployEvents: {
    next: (deploymentEvent) => {
      console.log(deploymentEvent);
    },
    error: (error) => {
      console.error(error);
    },
    complete: (contracts) => {
      console.log('*** Digital Asset deployment completed ***');
      console.log(contracts.LSP7DigitalAsset);
    },
  }
}));
