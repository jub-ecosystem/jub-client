from jub.dto.v2 import  DataSourceCreateDTO,DataRecordCreateDTO
from jub.client.v2 import JubClient

client = JubClient(api_url="http://localhost:5000",username="admin",password="admin")

async def create_datasource(datasource_name, datasource_type, datasource_url):
    datasource_create_dto = DataSourceCreateDTO(
        name           = datasource_name,
        description    = f"A {datasource_type} datasource created for testing.",
        format         = datasource_type,
    )
    datasource_result = await client.register_data_source(datasource_create_dto)
    if datasource_result.is_err:
        e = datasource_result.unwrap_err()
        print(e.response.content)
        print(f"Error creating datasource: {e}")
        return None
    datasource = datasource_result.unwrap()
    return datasource

async def add_records_to_datasource(source_id:str, path:str):
    # record_dtos = [DataRecordCreateDTO(**record) for record in records]
    result = await client.ingest_records_from_json(source_id, path)
    if result.is_err:
        print(f"Error adding records: {result.unwrap_err()}")
        return False
    return True


if __name__ == "__main__":
    import asyncio
    async def main():   
        datasource_name = "My CSV DataSource"
        datasource_type = "csv"
        datasource_url = "http://example.com/data.csv"
        data_records_path = "./data_records.json"

        datasource = await create_datasource(datasource_name, datasource_type, datasource_url)
        # print(f"Datasource created: {datasource}")
        if datasource:
            print(f"Datasource created: {datasource}")
            source_id = datasource.source_id
            if source_id:
                success = await add_records_to_datasource(source_id, data_records_path)
                if success:
                    print("Records added successfully.")
                else:
                    print("Failed to add records.")
            else:
                print("Datasource ID not found.")
    asyncio.run(main())