const conf = require('../config.json');
const express = require('express');
const app = express();
const port = 3000;
const Web3 = require('web3');
const web3 = new Web3(conf.rpc_endpoint);
const { ERC725 } = require('@erc725/erc725.js');
const { LSPFactory, LSP4DigitalAssetMetadata, LSP4Metadata } = require('@lukso/lsp-factory.js');
const LSP8Mintable = require('@lukso/lsp-smart-contracts/artifacts/LSP8Mintable.json');
const LSP7Mintable = require('@lukso/lsp-smart-contracts/artifacts/LSP7Mintable.json');
const LSP4schema = require("@erc725/erc725.js/schemas/LSP4DigitalAsset.json");
const LSP4 = require("@lukso/lsp-smart-contracts/artifacts/LSP4DigitalAssetMetadata.json");
const erc725schema = require('@erc725/erc725.js/schemas/LSP3UniversalProfileMetadata.json');
const provider = new Web3.providers.HttpProvider(conf.rpc_endpoint);
const myEOA = web3.eth.accounts.privateKeyToAccount(conf.private_key);
web3.eth.accounts.wallet.add(conf.private_key);
require('isomorphic-fetch');
const lspFactory = new LSPFactory(conf.rpc_endpoint, {
  deployKey: conf.private_key,
  chainId: 2828,
  ipfsGateway: conf.ipfs_gateway
});
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
const sqlite3 = require('sqlite3');
const db = new sqlite3.Database('./api.db');

app.get('/', (req, res) => {
    res.send('LUKSense API')
})

app.get('/get_transaction', async (req, res) => {
  info = await web3.eth.getTransactionReceipt(req.query['hash']);
  res.json(info);
})

app.get('/get_block', async (req, res) => {
  info = await web3.eth.getBlock(req.query['num']);
  res.json(info);
})

app.get('/get_balance', async (req, res) => {
  info = await web3.eth.getBalance(req.query['address']);
  res.json(info);
})

app.get('/get_message', async (req, res) => {
  db.get("SELECT message FROM validation WHERE up=? AND validation_time>=date('now', '-6 month') ORDER BY validation_time DESC LIMIT 1;", req.query['up'], function(err, data) {
    if (err) {
	    res.json({ 'message': null });
    } else {
      if (data == null){
	      const message = "verification string: " + (Math.random() + 1).toString(36).substring(7);
	      db.run("INSERT INTO validation(up, message) VALUES (?, ?);", 
		      [req.query['up'], message]);
	      res.json({ 'message': message });
      } else {
	      res.json(data);
      }
    }
  });
})

app.post('/is_signature_valid', async (req, res) => {
  try {
      db.get("SELECT message FROM validation WHERE up=? ORDER BY validation_time DESC;", req.body.address, async function(err, data) {
        if (err) {
	        res.json({ 'is_valid': false });
        } else {
          if (data == null){
	          res.json({ 'is_valid': false });
          } else {
            const messageHash = web3.eth.accounts.hashMessage(data['message']);
            const profile = new ERC725(erc725schema, req.body.address, provider, { ipfsGateway: conf.ipfs_gateway });
            const magic = await profile
              .isValidSignature(messageHash, req.body.signature);
            if (magic) {
              res.json({'is_valid': true});
            } else {
              res.json({'is_valid': false});
            }
          }
      }
    });
  } catch (error) {
    res.json({'is_valid': false});
  }
})

app.get('/fetch_up', async (req, res) => {
    try {
        const profile = new ERC725(erc725schema, req.query['up'], provider, { ipfsGateway: conf.ipfs_gateway });
        const data = await profile.fetchData('LSP3Profile');
	      res.json(data);
    } catch (error) {
        res.send(error);
    }
})

app.post('/upload_metadata', async (req, res) => {
    try {
	    const metaData = await LSP4DigitalAssetMetadata.uploadMetadata({
        	LSP4Metadata: {
          		description: req.body.description,
          		links: [{
            			title: req.body.name,
            			url: req.body.url
          		}]
        	}
	    });
	    res.json(metaData);
    } catch (error) {
	    res.send(error);
    }
})

app.post('/upload_metadata_json', async (req, res) => {
    try {
        const metaData = await LSP4DigitalAssetMetadata.uploadMetadata(req.body.meta);
        res.json(metaData);
    } catch (error) {
        res.send(error);
    }
})

app.get('/get_metadata', async (req, res) => {
    lsp4 = '0x9afb95cacc9f95858ec44aa8c3b685511002e30ae54415823f406128b85b238e'
    const getAssetData = async function(key, address) {
      try {
        const digitalAsset = new web3.eth.Contract(LSP4.abi, address);
        return await digitalAsset.methods["getData(bytes32)"](key).call();
      } catch (error) {
        return error;
      }
    }

    const decodeAssetData = async function(keyName, encodedData) {
      try {
        const digitalAsset = new ERC725(
          LSP4schema,
          req.query['lsp7'],
          provider,
          { ipfsGateway: conf.ipfs_gateway }
        );
        return digitalAsset.decodeData({
          keyName: keyName,
          value: encodedData,
        });
      } catch (error) {
        return error;
      }
    }

    const getMetaDataLink = async function(decodedAssetMetadata) {
      try {
        return decodedAssetMetadata.value.url.replace('ipfs://', conf.ipfs_gateway);
      } catch (error) {
        return error;
      }
    }

    const fetchAssetData = async function(dataURL) {
      try {
        const response = await fetch(dataURL);
        return await response.json();
      } catch (error) {
        return error;
      }
    }

    getAssetData(lsp4, req.query['lsp7']).then((encodedData) => {
      decodeAssetData(lsp4, encodedData).then((decodedData) => {
        getMetaDataLink(decodedData).then((dataURL) => {
          fetchAssetData(dataURL).then((assetJSON) => res.json(assetJSON));
        });
      });
    });
})

app.all('/change_metadata', async (req, res) => {
    
})

app.post('/new_lsp7', async (req, res) => {
    var lsp7 = {'status': 'error'};
    const nft = await lspFactory.LSP7DigitalAsset.deploy({
    	isNFT: true,
    	controllerAddress: myEOA.address,
    	name: req.body.name,
    	symbol: req.body.symbol,
    	creators: [req.body.creator],
    	digitalAssetMetadata: req.body.meta
    }, {
  	onDeployEvents: {
    		next: (deploymentEvent) => {
      			console.log(deploymentEvent);
    		},
    		error: (error) => {
      			console.error(error);
    		},
    		complete: (contracts) => {
      			lsp7 = contracts.LSP7DigitalAsset;
    		},
    	}
    });
    res.json(lsp7);
})

app.get('/mint_lsp8', async (req, res) => {
    const contract = new web3.eth.Contract(LSP8Mintable.abi, conf.lsp8);
    const minted = await contract.methods.mint(req.query['up'], req.query['lsp7'], true, '0x').send({
  	from: myEOA.address,
  	gas: 5_000_000,
  	gasPrice: '1000000000',
    });
    res.json(minted);
})

app.get('/mint_lsp7', async (req, res) => {
    const contract = new web3.eth.Contract(LSP7Mintable.abi, req.query['lsp7']);
    const minted = await contract.methods.mint(req.query['up'], 1, true, '0x').send({
        from: myEOA.address,
        gas: 5_000_000,
        gasPrice: '1000000000',
    });
    res.json(minted);
})

app.listen(port, () => {
    console.log(`LUKSense API listening on port ${port}`)
})
