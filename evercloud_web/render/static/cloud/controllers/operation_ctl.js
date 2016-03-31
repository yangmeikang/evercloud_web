'use strict';

CloudApp.controller('OperationController',
    function($rootScope, $scope, ngTableParams, ngTableHelper,
            CommonHttpService, DatePicker, Operation) {

    $scope.$on('$viewContentLoaded', function() {   
        Metronic.initAjax();
        DatePicker.initDatePickers();
    });

    $scope.condition = {operator: "", start_date: "", end_date: ""};
    var table = $scope.operation_table = new ngTableParams({
        page: 1,
        count: 10,
        filter: {}
    },{
        counts: [10, 20, 30, 40, 50],
        getData: function ($defer, params) {
            var filter = params.filter(),
                searchParams = {page: params.page(), page_size: params.count()};

            angular.extend(searchParams, filter);

            Operation.query(searchParams,
                function (data) {
                    ngTableHelper.countPages(params, data.count);
                    $defer.resolve(data.results);
                });
        }
    });

    $scope.search = function(){
        angular.copy($scope.condition, table.filter());
        table.page(1);
        table.reload();
    };

    $scope.reload = function(){
        table.reload();
        loadFilters();
    };

    $scope.keypress = function($event){
        if($event.keyCode == 13){
            $event.preventDefault();
            $scope.search();
        }
    };

    var loadFilters = function(){
        CommonHttpService.get('/api/operation/filters').then(function(filters){
            $scope.filters = filters;
        });
    };

   loadFilters();
});

