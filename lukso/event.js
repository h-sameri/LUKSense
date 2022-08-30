const conf = require('./config.json');
const UniversalProfile = require('@lukso/lsp-smart-contracts/artifacts/UniversalProfile.json');
const Web3 = require('web3');
const web3 = new Web3('https://rpc.l16.lukso.network');
const myUP = new web3.eth.Contract(UniversalProfile.abi, conf.up_address);
const sqlite3 = require('sqlite3');
const db = new sqlite3.Database('./api/api.db');
require("isomorphic-fetch");

db.get("SELECT block from last_block ORDER BY block DESC LIMIT 1;", (err, data) => {
        myUP.getPastEvents('ValueReceived', {fromBlock:data['block']+1, toBlock:'latest'}).then(result => {
                result.forEach(tx => {
                        var block = tx['blockNumber'];
                        var sender = tx['returnValues']['sender'];
                        var amount = parseInt(tx['returnValues']['value']);
                        amount = amount / 1_000_000_000_000_000_000;
                        console.log(block, sender, amount);
                        fetch("http://127.0.0.1:9000/transaction?" + new URLSearchParams({
                                sender: sender,
                                amount: amount.toString()
                        })).then(response => {
                                console.log(response.status);
                        }).then(data => {
                                // console.log(data);
                                db.run("INSERT INTO last_block (block) VALUES (?);", block, (err, data) => {
                                        // console.log(err);
                                });
                        }).catch(error => console.log(error));
                });
        });
});
