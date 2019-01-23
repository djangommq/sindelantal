## 使用说明

~~20180815~~  
**20180831**
1. 数据保存在 巴西0 的mongodb数据库
2. 每次启动前, 修改utils里的VERSION, 更新链接到新的表中
    ```python
    python3 update_links.py  # 将75个url下载后更新到数据库
    ```
3. 运行主体, 巴西0数据库环境, 巴西1运行list, 其他运行info
    ```python
    chmod +x run_list.sh
    chmod +x run_info.sh
    
    ./run_list.sh  
    ./run_info.sh
    
    # 先运行list, 等一段时间后其他服务器运行info即可
    ```
    
4. 进度跟踪
    ```python
    python3 statistics.py  # 显示当前进度
    ```
4. 结果验证
    运行
    ```python
    python3 count_restaurant_by_city.py
    ```    
    会按照城市(link)为单位统计餐馆的数量, 保存在sindelantal/sindelantal_statistic的表中, 手动查看, 是否有相差较大的数据, 修改数据库并重新运行
    **如果更新了数据库环境, 需要先运行里面的init方法, 手动修改运行**
        
5. 输出结果  
    ```python
    # comments位置: sindelantal/data/20180804/comments
    python3 output_csv.py
    # restaurant信息输出位置: sindelantal/data/20180804/restaurants/all.csv
    ```

6. 数据保存
    ```
        数据保存在巴西0上的mongo数据库中,运行脚本导出数据
    ```





