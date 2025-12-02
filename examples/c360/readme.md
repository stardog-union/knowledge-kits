A Knowledge Kit used for Stardog Training

## Customer 360

This Knowledge Kit contains a simple data model representing your typical e-commerce retailer who is interested in building a Customer 360 application to solve a particular problem, such as understanding churn or identifying loyal customers for auto enrollment in a discount program. 

You can find the raw data for this Kit [**on Github**](https://github.com/stardog-union/training/tree/main/designer).

### The Data Model

![schema](https://stardog-knowledge-kits.s3.amazonaws.com/training_c360/schema.png)

---

# Model Overview

## Classes 

### Class: Address

Properties: street address | city | state | zip code

### Class: Category

### Class: Credit Card

Properties: card holder | card type | card number

### Class: Customer

Properties: has rewards account | first name | last name | ssn | email | thumbnail | phone | has address

### Class: Industry

### Class: Order

Properties: rewards account used | price | quantity | date purchased | time purchased | purchased by | purchased | purchase card

### Class: Organization

### Class: Product

Properties: MSRP | description | in category | has vendor | thumbnail

### Class: Rewards Account
A concept representing a Customer's rewards account.

Properties: account id | opened date

### Class: Unit Price

Properties: has currency | has price

### Class: Vendor

Properties: in industry

---

## Properties

### Property: rewards account used
On Class: Order
Ranges: Rewards Account

### Property: has rewards account
On Class: Customer
Ranges: Rewards Account

### Property: card holder
On Class: Credit Card
Ranges: Customer

### Property: MSRP
On Class: Product
Ranges: Unit Price

### Property: in category
On Class: Product
Ranges: Category

### Property: has vendor
On Class: Product
Ranges: Vendor

### Property: purchased by
On Class: Order
Ranges: Customer

### Property: purchased
On Class: Order
Ranges: Product

### Property: purchase card
On Class: Order
Ranges: Credit Card

### Property: has address
On Class: Customer
Ranges: Address

### Property: in industry
On Class: Vendor
Ranges: Industry

### Property: account id
On Class: Rewards Account
Ranges: string

### Property: opened date
On Class: Rewards Account
Ranges: date

### Property: card type
On Class: Credit Card
Ranges: string

### Property: card number
On Class: Credit Card
Ranges: string

### Property: has currency
On Class: Unit Price
Ranges: string

### Property: has price
On Class: Unit Price
Ranges: float

### Property: description
On Class: Product
Ranges: string

### Property: price
On Class: Order
Ranges: decimal

### Property: quantity
On Class: Order
Ranges: integer

### Property: date purchased
On Class: Order
Ranges: date

### Property: time purchased
On Class: Order
Ranges: string

### Property: first name
On Class: Customer
Ranges: string

### Property: last name
On Class: Customer
Ranges: string

### Property: ssn
On Class: Customer
Ranges: string

### Property: email
On Class: Customer
Ranges: string

### Property: thumbnail
On Class: Customer | Product
Ranges: string

### Property: phone
On Class: Customer
Ranges: string

### Property: street address
On Class: Address
Ranges: string

### Property: city
On Class: Address
Ranges: string

### Property: state
On Class: Address
Ranges: string

### Property: zip code
On Class: Address
Ranges: string