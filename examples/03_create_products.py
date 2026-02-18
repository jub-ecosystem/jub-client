import sys 
from jub.client import JubClient,LevelCatalog,Product,Level
from uuid import uuid4

oca_client = JubClient(
    hostname = "localhost",
    port     = 5000
)


def main():
    obid = sys.argv[1]
    cid = sys.argv[2]
    p = Product(
            pid         = uuid4().hex.replace("-",""),
            description = "No description yet.",
            level_path  = "CIE10.SEX.PLOT_TYPE",
            levels      = [
                Level(
                    cid   = cid,
                    index = 0,
                    kind  = "INTEREST",
                    value = "HOMBRE",
                )
            ],
            product_name = "Test Product",
            product_type = "PRODUCT_TYPE",
            profile      = "HOMBRE",
            tags         = [obid],
            url          = "https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExZzFsdnlsNGY3ZGFwNjhmeTRhYWU3eG1jMDMxZ2t2dmE3Yjg2NjFoZyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/VbnUQpnihPSIgIXuZv/giphy.gif",
    )
    
    result = oca_client.create_products(products=[p])
    if result.is_ok:
        print("Products created successfully")
    else:
        print(f"Failed to create products: {result.unwrap_err()}")


if __name__ == "__main__":
    main()