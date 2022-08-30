const conf = require('./config.json');
const LSP8Mintable = require('@lukso/lsp-smart-contracts/artifacts/LSP8Mintable.json');
const Web3 = require('web3');
const web3 = new Web3(conf.rpc_endpoint);
const myEOA = web3.eth.accounts.privateKeyToAccount(conf.private_key);
web3.eth.accounts.wallet.add(conf.private_key);
const contract = new web3.eth.Contract(LSP8Mintable.abi, conf.lsp8);

var owner = conf.up_address;
var nft = '0x';

process.argv.forEach(function (val, index, array) {
  if (val.startsWith("owner=")){
    owner = val.split('=')[1];
  } else if (val.startsWith("nft=")){
    nft = val.split('=')[1];
  }
});

contract.methods.mint(owner, nft, false, '0x').send({
  from: myEOA.address,
  gas: 5_000_000,
  gasPrice: '1000000000',
}).then(r => console.log(r));
