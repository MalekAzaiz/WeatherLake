import azure.functions as func
import logging
import sys
import os

# sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

app = func.FunctionApp()


@app.route(route="fetch_and_upload", auth_level=func.AuthLevel.FUNCTION)
def fetch_and_upload(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('fetch_and_upload triggered')
    try:
        from ingestion.fetch_and_upload import main
        main()
        return func.HttpResponse("fetch_and_upload OK", status_code=200)
    except Exception as e:
        logging.error(str(e))
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)


@app.route(route="raw_to_silver", auth_level=func.AuthLevel.FUNCTION)
def raw_to_silver(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('raw_to_silver triggered')
    try:
        from processing.raw_to_silver import main
        main()
        return func.HttpResponse("raw_to_silver OK", status_code=200)
    except Exception as e:
        logging.error(str(e))
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)


@app.route(route="silver_to_gold", auth_level=func.AuthLevel.FUNCTION)
def silver_to_gold(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('silver_to_gold triggered')
    try:
        from processing.silver_to_gold import main
        main()
        return func.HttpResponse("silver_to_gold OK", status_code=200)
    except Exception as e:
        logging.error(str(e))
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)