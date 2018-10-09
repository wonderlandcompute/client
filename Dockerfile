FROM conda/miniconda3
#prerequirements
RUN apt-get update \
    && apt-get install -y \
    git-core \
    make
RUN apt-get install -y libffi-dev g++ libssl-dev
RUN pip --no-cache-dir install jupyter \
    && pip --no-cache-dir install google \
    && pip --no-cache-dir install protobuf \
    && conda install -c conda-forge ipywidgets
#RUN pip uninstall -y xgboost \
#    && git clone --recursive https://github.com/dmlc/xgboost \
#    && cd xgboost \
#    && git checkout tags/0.47 \
#    && make -j4 \
#    && python python-package/setup.py install
RUN pip --no-cache-dir install azure-storage-file


#modelgym installing
RUN git clone https://github.com/igormusinov/modelgym \
    && cd /modelgym && git checkout sync+afs_transfer \
    && pip --no-cache-dir install -r requirements.txt \
    && pip --no-cache-dir install -e .

#wonderClient installing
COPY . /wonderclient
RUN mkdir ~/.wonder
COPY config.yaml /root/.wonder/config.yaml
COPY certs/* /certs/
RUN pip --no-cache-dir install -e /wonderclient

EXPOSE 8888
RUN mkdir ~/repo-storage && umask o+w
ENTRYPOINT jupyter notebook --ip=0.0.0.0 --allow-root --notebook-dir="/wonderclient/examples/hyperoptimisation" --NotebookApp.token=''
