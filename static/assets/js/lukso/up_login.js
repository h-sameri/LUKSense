// const onSignatureValidation = async () => {
//   const erc725AccountAddress = getState("address");
//
//   if (!erc725AccountAddress) {
//     return setNotification("No valid address", "danger");
//   }
//
//   try {
//     const messageHash = getWeb3().eth.accounts.hashMessage(message.value);
//     if (window.erc725Account) {
//       // TODO: we should probably set the default gas price to undefined,
//       // but it is not yet clear why view functions error on L16 when gasPrice is passed
//       window.erc725Account.options.gasPrice = void 0;
//       magicValue.value = (await window.erc725Account.methods
//         .isValidSignature(messageHash, signResponse.value.signature)
//         .call()) as string;
//     }
//
//     if (magicValue.value === MAGICVALUE) {
//       setNotification(`Signature validated successfully`, "info");
//     } else {
//       setNotification("Response doesn't match magic value", "danger");
//     }
//   } catch (error) {
//     setNotification((error as unknown as Error).message, "danger");
//   }
// };
//
// 0x224fcBf885495f0fB7aBB0df56F63562572e215E

const web3 = new Web3(window.ethereum);
web3.eth.getAccounts();
let UP_ADDRESS= '0x36B42FFa60937a96464D8D04C573e90c95526d07'
web3.eth.sign('test', UP_ADDRESS);
