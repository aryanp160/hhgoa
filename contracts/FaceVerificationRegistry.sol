// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title FaceVerificationRegistry
 * @dev Smart contract for storing and verifying facial recognition & social post records on-chain.
 * Provides tamper-evident proof of discovered web content matching input face scans.
 */
contract FaceVerificationRegistry {
    
    struct Record {
        bytes32 dataHash;        // SHA-256 fingerprint of (face_hash + post_url + post_hash)
        string faceHash;         // SHA-256 of facial crop image
        string postUrl;          // Discovered social media post URL
        string postHash;         // Cryptographic hash of social post content/image
        string metadataUri;      // Additional metadata (JSON string or IPFS URI)
        uint256 timestamp;       // On-chain registration timestamp
        address registrar;       // Account address that submitted the proof
        bool exists;             // Flag indicating record existence
    }

    // Mapping from dataHash => Record
    mapping(bytes32 => Record) private records;
    
    // Array storing all registered dataHashes for iteration/audit
    bytes32[] private dataHashList;

    // Events
    event RecordRegistered(
        bytes32 indexed dataHash,
        string faceHash,
        string postUrl,
        address indexed registrar,
        uint256 timestamp
    );

    /**
     * @dev Register a new face & post verification record on the blockchain.
     */
    function registerVerification(
        bytes32 dataHash,
        string memory faceHash,
        string memory postUrl,
        string memory postHash,
        string memory metadataUri
    ) public returns (bool) {
        require(dataHash != bytes32(0), "Data hash cannot be empty");
        require(!records[dataHash].exists, "Record already registered on-chain");

        records[dataHash] = Record({
            dataHash: dataHash,
            faceHash: faceHash,
            postUrl: postUrl,
            postHash: postHash,
            metadataUri: metadataUri,
            timestamp: block.timestamp,
            registrar: msg.sender,
            exists: true
        });

        dataHashList.push(dataHash);

        emit RecordRegistered(
            dataHash,
            faceHash,
            postUrl,
            msg.sender,
            block.timestamp
        );

        return true;
    }

    /**
     * @dev Verify if a dataHash exists on-chain and retrieve its full record.
     */
    function verifyRecord(bytes32 dataHash) public view returns (
        bool exists,
        uint256 timestamp,
        address registrar,
        string memory faceHash,
        string memory postUrl,
        string memory postHash,
        string memory metadataUri
    ) {
        Record memory rec = records[dataHash];
        require(rec.exists, "Record not found on blockchain");

        return (
            rec.exists,
            rec.timestamp,
            rec.registrar,
            rec.faceHash,
            rec.postUrl,
            rec.postHash,
            rec.metadataUri
        );
    }

    /**
     * @dev Check if a dataHash is registered without reverting.
     */
    function isDataHashRegistered(bytes32 dataHash) public view returns (bool) {
        return records[dataHash].exists;
    }

    /**
     * @dev Total number of registered verification records.
     */
    function getRecordCount() public view returns (uint256) {
        return dataHashList.length;
    }

    /**
     * @dev Retrieve dataHash by index.
     */
    function getDataHashAtIndex(uint256 index) public view returns (bytes32) {
        require(index < dataHashList.length, "Index out of bounds");
        return dataHashList[index];
    }
}
