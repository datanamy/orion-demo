from pathlib import Path

from prefect.deployments import Deployment

import flows.dask_flow
import flows.param_flow
import flows.storage

# `prefect deployment build` does not allow parameters to be specified
# so we use build_from_flow instead
# see https://github.com/PrefectHQ/prefect/issues/6304


# upload flow to storage and create deployment yaml file
deployment: Deployment = Deployment.build_from_flow(
    name="s3",
    flow=flows.param_flow.increment,
    output="deployment-increment-s3.yaml",
    # Deployment class args
    description="deployment using s3 storage",
    version="snapshot",
    work_queue_name="kubernetes",
    # every deployment will overwrite the files in this location
    storage=flows.storage.minio_flows_increment(),
    # override the default KubernetesJob
    infra_overrides=dict(
        image="orion-registry:5000/flow:latest",
        # use to read the stored flow from minio when the flow executes
        # TODO: move into kubes environment to avoid storing secrets in Prefect
        env={"AWS_ACCESS_KEY_ID": "minioadmin", "AWS_SECRET_ACCESS_KEY": "minioadmin"},
    ),
    parameters={"i": 1},
)  # type: ignore


def fix_entrypoint(entrypoint: str) -> str:
    # Workaround until https://github.com/PrefectHQ/prefect/issues/6469 is resolved
    flow_path, flow = entrypoint.split(":")
    flow_path = Path(flow_path).relative_to(Path(".").absolute())
    return f"{flow_path}:{flow}"


if __name__ == "__main__":
    deployment.entrypoint = fix_entrypoint(deployment.entrypoint)
    id = deployment.apply()
    print(f"Deployment {id} created.")


# Requires a docker image with prefect-dask & dask_kubernetes.
# Deployment(
#     name="orion-packager",
#     flow=flows.dask_flow.greetings,
#     infrastructure=KubernetesJob(
#         image="orion-registry:5000/flow:latest",
#     ),
#     parameters={"names": ["kubes", "deployment!"]},
# )