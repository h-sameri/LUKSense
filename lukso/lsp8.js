const conf = require('./config.json');
const LSP8Mintable = require('@lukso/lsp-smart-contracts/artifacts/LSP8Mintable.json');
const Web3 = require('web3');
const web3 = new Web3(conf.rpc_endpoint);
const myEOA = web3.eth.accounts.privateKeyToAccount(conf.private_key);

web3.eth.accounts.wallet.add(conf.private_key);

const tokenParams = [
    'LUKSense',
    'LUKS',
    myEOA.address
];

const myToken = new web3.eth.Contract(LSP8Mintable.abi, {
    gas: 5_000_000,
    gasPrice: '1000000000',
});

myToken.deploy({ data: LSP8Mintable.bytecode, arguments: tokenParams }).send({from: myEOA.address})
	.then(deployed => console.log(deployed._address));
