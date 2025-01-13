FROM public.ecr.aws/lambda/python:3.13

#req
COPY requirements_model.txt ${LAMBDA_TASK_ROOT}

RUN pip install -r requirements_model.txt
COPY src/* ${LAMBDA_TASK_ROOT}

CMD [ "main.handler" ]
