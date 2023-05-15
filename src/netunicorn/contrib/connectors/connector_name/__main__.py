import json
import os
from typing import Dict, List, Literal, Optional, TypeAlias, TypedDict, Union

import uvicorn
from fastapi import FastAPI, Header, HTTPException, Request, Depends, status
from fastapi.openapi.models import Response
from fastapi.security import OAuth2PasswordBearer

from netunicorn.base.deployment import Deployment
from netunicorn.base.types import DeploymentRepresentation, NodeRepresentation
from netunicorn.base.utils import UnicornEncoder
from pydantic import BaseModel

from .connector import ConnectorTemplate

OperationContext: TypeAlias = Optional[str]


class StopExecutorRequest(TypedDict):
    executor_id: str
    node_name: str


class ResultData(TypedDict):
    type: Literal["success", "failure"]
    data: Optional[str]


API_KEY = os.environ["NETUNICORN_API_KEY"]
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def api_key_auth(api_key: str = Depends(oauth2_scheme)):
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Forbidden"
        )


app = FastAPI()

connector = ConnectorTemplate(
    connector_name="name",
    configuration=None,
    netunicorn_gateway="",
    logger=None,
)


class HealthResponse(BaseModel):
    status: str


# using original types from netunicorn.base.types introduce recursion during type inference from pydantic
class NodesRepresentation(BaseModel):
    node_pool_type: str
    node_pool_data: List[Union[NodeRepresentation, "NodesRepresentation"]]


async def parse_context(json_str: Optional[str]) -> Optional[dict[str, str]]:
    if not json_str or json_str == "null":
        return None
    try:
        return json.loads(json_str)  # type: ignore
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Couldn't parse the context: {e}",
        )


@app.post("/initialize", status_code=204, dependencies=[Depends(api_key_auth)])
async def init(request: Request) -> None:
    body = json.loads(await request.body())
    if body:
        try:
            await connector.initialize(**body)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Couldn't initialize the connector: {e}",
            )


@app.get("/health", status_code=200, responses={500: {"model": HealthResponse}}, dependencies=[Depends(api_key_auth)])
async def health() -> HealthResponse:
    healthy, text = await connector.health()
    response = HealthResponse(status=text)
    if not healthy:
        raise HTTPException(
            status_code=500,
            detail=response,
        )
    return response


@app.post("/shutdown", status_code=204, dependencies=[Depends(api_key_auth)])
async def shutdown() -> None:
    await connector.shutdown()


@app.get("/nodes/{username}", status_code=200, dependencies=[Depends(api_key_auth)])
async def get_nodes(
    username: str,
    netunicorn_auth_context: OperationContext = Header(default=None),
) -> NodeRepresentation:
    auth_context = await parse_context(netunicorn_auth_context)
    node_pool = await connector.get_nodes(username, auth_context)
    json_str = json.dumps(node_pool, cls=UnicornEncoder)
    return Response(media_type="application/json", content=json_str)  # type: ignore


@app.post("/deploy/{username}/{experiment_id}", status_code=200, dependencies=[Depends(api_key_auth)])
async def deploy(
    username: str,
    experiment_id: str,
    deployments_data: List[DeploymentRepresentation],
    netunicorn_auth_context: OperationContext = Header(default=None),
    netunicorn_deployment_context: OperationContext = Header(default=None),
) -> Dict[str, ResultData]:
    auth_context = await parse_context(netunicorn_auth_context)
    deployment_context = await parse_context(netunicorn_deployment_context)
    deployments = [Deployment.from_json(x) for x in deployments_data]

    result = await connector.deploy(
        username=username,
        experiment_id=experiment_id,
        deployments=deployments,
        deployment_context=deployment_context,
        authentication_context=auth_context,
    )

    json_str = json.dumps(result, cls=UnicornEncoder)
    return Response(media_type="application/json", content=json_str)  # type: ignore


@app.post("/execute/{username}/{experiment_id}", status_code=200, dependencies=[Depends(api_key_auth)])
async def execute(
    username: str,
    experiment_id: str,
    deployments_data: List[DeploymentRepresentation],
    netunicorn_auth_context: OperationContext = Header(default=None),
    netunicorn_execution_context: OperationContext = Header(default=None),
) -> Dict[str, ResultData]:
    auth_context = await parse_context(netunicorn_auth_context)
    execution_context = await parse_context(netunicorn_execution_context)
    deployments = [Deployment.from_json(x) for x in deployments_data]

    result = await connector.execute(
        username=username,
        experiment_id=experiment_id,
        deployments=deployments,
        execution_context=execution_context,
        authentication_context=auth_context,
    )

    json_str = json.dumps(result, cls=UnicornEncoder)
    return Response(media_type="application/json", content=json_str)  # type: ignore


@app.post("/stop_executors/{username}", status_code=200, dependencies=[Depends(api_key_auth)])
async def stop_executors(
    username: str,
    requests_list: List[StopExecutorRequest],
    netunicorn_auth_context: OperationContext = Header(default=None),
    netunicorn_cancellation_context: OperationContext = Header(default=None),
) -> Dict[str, ResultData]:
    auth_context = await parse_context(netunicorn_auth_context)
    cancellation_context = await parse_context(netunicorn_cancellation_context)
    result = await connector.stop_executors(
        username=username,
        requests_list=requests_list,
        cancellation_context=cancellation_context,
        authentication_context=auth_context,
    )
    json_str = json.dumps(result, cls=UnicornEncoder)
    return Response(media_type="application/json", content=json_str)  # type: ignore


@app.post("/cleanup/{experiment_id}", status_code=200, dependencies=[Depends(api_key_auth)])
async def cleanup(
    experiment_id: str,
    deployments_data: List[DeploymentRepresentation],
) -> None:
    deployments = [Deployment.from_json(x) for x in deployments_data]
    await connector.cleanup(experiment_id, deployments)

uvicorn.run(app)
