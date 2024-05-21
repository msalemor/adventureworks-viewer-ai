SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

CREATE view [SalesLT].[vCustomers]
as
    select A.*, B.Orders, B.TotalDue
    from
        (
select a.CustomerID, A.LastName, a.FirstName, a.EmailAddress, a.SalesPerson, c.City, c.StateProvince, c.CountryRegion
        from SalesLt.Customer A
            left outer join
            SalesLT.CustomerAddress B
            on b.CustomerID=a.CustomerID and b.AddressType='main office'
            left outer join
            SalesLT.Address C
            on c.AddressID=B.AddressID
) A
        left outer join
        (select CustomerID, count(*) Orders, sum(TotalDue) TotalDue
        from SalesLT.SalesOrderHeader
        group by CustomerID) B
        on b.CustomerID=a.CustomerID
GO

CREATE VIEW [SalesLT].[vTopCustomers]
AS
    select A.CustomerID, b.LastName, B.FirstName, B.EmailAddress, b.SalesPerson, A.Total, D.City, D.StateProvince, D.CountryRegion
    from (
select A.CustomerID, sum(a.TotalDue) Total
        from SalesLT.SalesOrderHeader A
        GROUP by a.CustomerID
) A
        inner join
        SalesLT.Customer B
        on A.CustomerID = b.CustomerID
        inner JOIN
        SalesLT.CustomerAddress C
        on A.CustomerID=c.CustomerID and c.AddressType='main office'
        inner JOIN
        SalesLT.Address D
        on c.AddressID=d.AddressID
GO

-- CREATE VIEW [SalesLT].[vProductAndDescription]
-- WITH
--     SCHEMABINDING
-- AS
--     -- View (indexed or standard) to display products and product descriptions by language.
--     SELECT
--         p.[ProductID]
--     , p.[Name]
--     , pm.[Name] AS [ProductModel]
--     , pmx.[Culture]
--     , pd.[Description]
--     FROM [SalesLT].[Product] p
--         INNER JOIN [SalesLT].[ProductModel] pm
--         ON p.[ProductModelID] = pm.[ProductModelID]
--         INNER JOIN [SalesLT].[ProductModelProductDescription] pmx
--         ON pm.[ProductModelID] = pmx.[ProductModelID]
--         INNER JOIN [SalesLT].[ProductDescription] pd
--         ON pmx.[ProductDescriptionID] = pd.[ProductDescriptionID];
-- GO

--CREATE UNIQUE CLUSTERED INDEX [IX_vProductAndDescription] ON [SalesLT].[vProductAndDescription]
--(
--	[Culture] ASC,
--	[ProductID] ASC
--)WITH (STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, DROP_EXISTING = OFF, ONLINE = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
--GO

CREATE VIEW [SalesLT].[vOrderDetails]
AS
    select b.CustomerID, A.SalesOrderID, A.ProductID, D.Name Category, E.Name Model, G.[Description], A.OrderQty, A.UnitPrice, A.UnitPriceDiscount, A.LineTotal
    from SalesLT.SalesOrderDetail A
        inner join
        SalesLT.SalesOrderHeader B
        on A.SalesOrderID = b.SalesOrderID
        inner JOIN
        SalesLT.Product C
        on A.ProductID=c.ProductID
        inner join
        SalesLT.ProductCategory D
        on c.ProductCategoryID=d.ProductCategoryID
        inner join
        SalesLT.ProductModel E
        on c.ProductModelID=e.ProductModelID
        INNER join
        SalesLT.ProductModelProductDescription F
        on f.ProductModelID=e.ProductModelID and f.Culture='en'
        inner join
        SalesLT.ProductDescription G
        on g.ProductDescriptionID = f.ProductDescriptionID
GO

CREATE VIEW [SalesLT].[vTopProductsSold]
AS
    select ProductId, category, model, [description], sum(orderqty) TotalQty
    from SalesLT.vOrderDetails
    group by productid,category,model,[description]
GO
