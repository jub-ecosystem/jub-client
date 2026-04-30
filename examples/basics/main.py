import asyncio
import os
from jub.client.v2 import JubClient,JubClientBuilder
import jub.dto.v2 as DTO
from uuid import uuid4
async def main():
    iid = uuid4().hex[:6]
    observatory_id = f"observatorio-de-prueba-{iid}"
    # Paso 1: Crear el cliente
    result = await JubClientBuilder(
            api_url  = os.environ.get("JUB_API_URL",  "http://localhost:5000"),
            # api_url  = os.environ.get("JUB_API_URL",  "https://apix.tamps.cinvestav.mx/jub"),
            username = os.environ.get("JUB_USERNAME", "invitado"),
            password = os.environ.get("JUB_PASSWORD", "invitado"),
        ).build()
    #  Paso 2: Manejar el resultado de la autenticación
    if result.is_err:
        print(f"Error creating client: {result.unwrap_err()}")
        raise result.unwrap_err()
    # Paso 3: Extraer el cliente del resultado exitoso
    client: JubClient = result.unwrap()
    print(f"Connected  user_id={client.user_id}")
    # Paso 4: Calendarizar la creacion de un observatorio
    
    setup_result = await client.setup_observatory(
        dto=DTO.ObservatorySetupDTO(
            observatory_id = observatory_id,
            title          = "Observatorio de Prueba",
            description    = "Un observatorio creado para probar la funcionalidad de JubClient.",
            image_url      = "", 
            metadata       = {"llave1": "valor1", "llave2": "valor2"}
        )
    )
    # Paso 5: Manejar el resultado de la calendarizacion del observatorio
    if setup_result.is_err:
        print(f"Error setting up observatory: {setup_result.unwrap_err()}")
        raise setup_result.unwrap_err()
    
    # T.sleep(10000)
    

    # Paso 6: Extraer la respuesta del resultado exitoso y mostrar el task_id (es importante para seguir el progreso de la tarea)
    setup_response = setup_result.unwrap()
    task_id        = setup_response.task_id
    print(f"Observatory setup successfully: task_id={task_id}")
    
    # Paso 7: Indexar catalogos y enlazarlos a un observatorio
    catalogs_result = await client.create_bulk_catalogs_and_link_from_json(
        json_path= "examples/basics/catalogs.json",
        observatory_id=observatory_id
    )

    if catalogs_result.is_err:
        print(f"Error creating catalogs: {catalogs_result.unwrap_err()}")
        raise catalogs_result.unwrap_err()
    print(f"Catalogs created successfully: {catalogs_result.unwrap()}")

    # Paso 8: Indexar productos
    product_id = "producto-de-prueba"
    product_result = await client.create_product(
        dto = DTO.ProductCreateDTO(
            product_id=product_id,
            name="Producto de Prueba",
            description="Un producto creado para probar la funcionalidad de JubClient.",
            observatory_id=observatory_id,
            catalog_item_ids=["MALE","Y2000"], # Los identificadores de items son los que hacen posible la busqueda. Por favor asegurate de que los items existan o cuando crees un catalogo y sus items, asignales identificadores que puedas usar para enlazar productos.
        )
    )

    if product_result.is_err:
        print(f"Error creating product: {product_result.unwrap_err()}")
        raise product_result.unwrap_err()
    print(f"Product created successfully: {product_result.unwrap()}")
    #  Paso 8: Cargar datos al producto
    data_result = await client.upload_product(
        file_path="/source/heatmap.html",
        product_id=product_id,
    )
    if data_result.is_err:
        print(f"Error uploading product data: {data_result.unwrap_err()}")
        raise data_result.unwrap_err()
    print(f"Product data uploaded successfully: {data_result.unwrap()}")

    # Paso 9: Asignar tags a un producto
    #
    task_result = await client.complete_task(
        task_id=task_id,
        dto=DTO.TaskCompleteDTO(
            success=True,
            message="Tarea completada exitosamente. El observatorio está listo para ser explorado.",
            # message="Simulando un error en la tarea de creación del observatorio.",
        )
    )
    print(f"Task completion result: {task_result}")

if __name__ == "__main__":    
    asyncio.run(main())