FROM public.ecr.aws/lambda/python:3.12

#req
COPY requirements_model.txt ${LAMBDA_TASK_ROOT}

RUN pip install -r requirements_model.txt
COPY src/* ${LAMBDA_TASK_ROOT}
COPY models/* ${LAMBDA_TASK_ROOT}
CMD [ "lambda_function.lambda_handler" ]
