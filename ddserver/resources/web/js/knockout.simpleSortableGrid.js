(function () {
    // Private function
    function getColumnsForScaffolding(data) {
        if ((typeof data.length !== 'number') || data.length === 0) {
            return [];
        }
        var columns = [];
        for (var propertyName in data[0]) {
            columns.push({ headerText: propertyName, rowText: propertyName });
        }
        return columns;
    }

    ko.simpleSortableGrid = {
        // Defines a view model class you can use to populate a grid
        viewModel: function (configuration) {
            var self = this;

            this.data = configuration.data;
            this.currentPageIndex = ko.observable(0);
            this.pageSize = configuration.pageSize || 5;
            this.sortByClass = configuration.sortByClass || 'fa fa-sort';
            this.sortByClassAsc = configuration.sortByClassAsc || 'fa fa-caret-up';
            this.sortByClassDesc = configuration.sortByClassDesc || 'fa fa-caret-down';

            this.lastSortedColumn = ko.observable('');
            this.lastSort = ko.observable('Desc');

            // If you don't specify columns configuration, we'll use scaffolding
            this.columns = configuration.columns || getColumnsForScaffolding(ko.unwrap(this.data));

            this.itemsOnCurrentPage = ko.computed(function () {
                var startIndex = this.pageSize * this.currentPageIndex();
                return ko.unwrap(this.data).slice(startIndex, startIndex + this.pageSize);
            }, this);

            this.maxPageIndex = ko.computed(function () {
                return Math.ceil(ko.unwrap(this.data).length / this.pageSize) - 1;
            }, this);

            this.sortBy = function (columnName) {
                if (self.lastSortedColumn() != columnName) {
                    self.sortByAsc(columnName);
                    self.lastSortedColumn(columnName);
                    self.lastSort('Asc');
                } else if (self.lastSort() == 'Asc') {
                    self.sortByDesc(columnName);
                    self.lastSort('Desc');
                } else {
                    self.sortByAsc(columnName);
                    self.lastSort('Asc');
                }
                self.currentPageIndex(0);
            };
            this.sortByAsc = function (columnName) {
                self.data.sort(function (a, b) {
                    return a[columnName] < b[columnName] ? -1 : 1;
                });
            };
            this.sortByDesc = function (columnName) {
                self.data.reverse(function (a, b) {
                    return a[columnName] < b[columnName] ? -1 : 1;
                });
            };
            this.sortByCSS = function (columnName) {
                if (columnName != undefined && columnName != '') {
                    return self.lastSortedColumn() == columnName ? (self.lastSort() == 'Asc' ? self.sortByClassAsc : self.sortByClassDesc) : self.sortByClass;
                } else {
                    return '';
                }
            };
        }
    };

    // Templates used to render the grid
    var templateEngine = new ko.nativeTemplateEngine();

    templateEngine.addTemplate = function (templateName, templateMarkup) {
        document.write("<script type='text/html' id='" + templateName + "'>" + templateMarkup + "<" + "/script>");
    };

    // Default template for displaying data tables
    templateEngine.addTemplate("pageGridTemplateDefault", "\
        <table class=\"table table-striped table-hover\">\
            <thead>\
                <tr data-bind=\"foreach: columns\" style=\"cursor:pointer;\">\
                    <!-- ko if: isSortable == true-->\
                    <th data-bind=\"click:$parent.sortBy($data.rowText)\">\
                        <span data-bind=\"text: headerText\"></span>\
                        <span data-bind=\"css:$parent.sortByCSS($data.rowText)\"></span>\
                    </th>\
                    <!-- /ko -->\
                    <!-- ko ifnot: isSortable == true-->\
                    <th><span data-bind=\"text: headerText\"></span></th>\
                    <!-- /ko -->\
                </tr>\
            </thead>\
            <tbody data-bind=\"foreach: itemsOnCurrentPage\">\
               <tr data-bind=\"foreach: $parent.columns\">\
                   <td data-bind=\"text: typeof rowText == 'function' ? rowText($parent) : $parent[rowText] \"></td>\
                </tr>\
            </tbody>\
        </table>\
    ");

    // Default template for displaying the page navigation
    templateEngine.addTemplate("pageLinksTemplateDefault", "\
        <div style=\"text-align: center;\">\
          <nav style=\"border-top: 1px solid #ddd;\">\
            <ul class=\"pagination pagination-sm\">\
              <li data-bind=\"css: { disabled: $root.currentPageIndex() == 0 }\">\
                <a href=\"#\" data-bind=\"click: function() { if($root.currentPageIndex() > 0) $root.currentPageIndex(0) }\">First</a>\
              </li>\
              <li data-bind=\"css: { disabled: $root.currentPageIndex() == 0 }\">\
                <a href=\"#\" data-bind=\"click: function() { if($root.currentPageIndex() > 0) $root.currentPageIndex($root.currentPageIndex() - 1) }\">\Previous</a>\
              </li>\
              <li>\
                <span data-bind=\"text: ($root.currentPageIndex() + 1) + ' of ' + ($root.maxPageIndex() + 1)\"></span>\
              </li>\
              <li data-bind=\"css: { disabled: $root.currentPageIndex() == $root.maxPageIndex() }\">\
                <a href=\"#\" data-bind=\"click: function() { if($root.currentPageIndex() < $root.maxPageIndex()) $root.currentPageIndex($root.currentPageIndex() + 1) }\">Next</a>\
              </li>\
              <li data-bind=\"css: { disabled: $root.currentPageIndex() == $root.maxPageIndex() }\">\
                <a href=\"#\" data-bind=\"click: function() { if($root.currentPageIndex() < $root.maxPageIndex()) $root.currentPageIndex($root.maxPageIndex()) }\">Last</a>\
              </li>\
            </ul>\
          </nav>\
        </div>\
    ");

    // The "simpleSortableGrid" binding
    ko.bindingHandlers.simpleSortableGrid = {
        init: function () {
            return { 'controlsDescendantBindings': true };
        },
        // This method is called to initialize the node, and will also be called again if you change what the grid is bound to
        update: function (element, viewModelAccessor, allBindings) {
            var viewModel = viewModelAccessor();

            // Empty the element
            while (element.firstChild)
                ko.removeNode(element.firstChild);

            // Get the templates
            var gridTemplateName = allBindings.get('simpleSortableGridTemplate') || "pageGridTemplateDefault",
                pageLinksTemplateName = allBindings.get('simpleSortableGridPagerTemplate') || "pageLinksTemplateDefault";

            // Render the main grid
            var gridContainer = element.appendChild(document.createElement("DIV"));
            ko.renderTemplate(gridTemplateName, viewModel, { templateEngine: templateEngine }, gridContainer, "replaceNode");

            // Render the page links
            if(viewModel.maxPageIndex() > 0) {
              var pageLinksContainer = element.appendChild(document.createElement("DIV"));
              ko.renderTemplate(pageLinksTemplateName, viewModel, { templateEngine: templateEngine }, pageLinksContainer, "replaceNode");
            }
        }
    };
})();