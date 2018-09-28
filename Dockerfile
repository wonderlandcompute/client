FROM conda/miniconda3
RUN apt-get update \
    && apt-get install -y \
    git-core \
    make
RUN apt-get install -y libffi-dev g++ libssl-dev
RUN git clone https://github.com/igormusinov/modelgym \
    && cd /modelgym && git checkout sync+afs_transfer \
    && pip --no-cache-dir install -r requirements.txt \
    && pip --no-cache-dir install -e . 
RUN pip --no-cache-dir install jupyter \
    && pip --no-cache-dir install google \
    && pip --no-cache-dir install protobuf \
    && conda install -c conda-forge ipywidgets \
    && conda install -y tornado==4.5.3
RUN pip uninstall -y xgboost \
    && git clone --recursive https://github.com/dmlc/xgboost \
    && cd xgboost \
    && git checkout tags/0.47 \
    && make -j4 \
    && python python-package/setup.py install 

RUN pip install azure-storage-file

#Be sure in wonderclient version
COPY . /wonderclient
COPY certs/* /certs/
RUN pip --no-cache-dir install -e /wonderclient

EXPOSE 8888
RUN mkdir ~/repo-storage && umask o+w
ENTRYPOINT jupyter notebook --ip=0.0.0.0 --allow-root
