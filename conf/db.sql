create table account (
    name varchar(100),
    balance float not NULL,
    creditAllowed boolean,
    status varchar(1),
    creditLimit float NOT NULL,
    profitPercentage float not NULL);

create table ledger (
    id int(11) NOT NULL AUTO_INCREMENT,
    time datetime NOT NULL,
    description varchar(256),
    accountName varchar(50),
    refId varchar(100),
    mobileNo varchar(20),
    sender varchar(20),
    operator varchar(20),
    type varchar(50),
    country varchar(20),
    product varchar(20),
    amount float,
    balance float,
    entryMadeBy varchar(100),
    uniqueKey varchar(200),
    retailPrice float,
    wholeSalePrice float,
    serviceFee float,
    destinationCurrency varchar(200),
    agentPrice float,
    reason varchar(255),
    status varchar(255)
    PRIMARY KEY (`id`) );